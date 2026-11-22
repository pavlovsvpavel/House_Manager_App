from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.clients.models import Client
from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.houses.models import House

UserModel = get_user_model()


class HouseOwnershipTests(TestCase):
    """
    Regression tests for the Phase 0 + Redesign Phase 1 security model:
    - ownership is derived from the URL on every request;
    - foreign houses return 404 and never touch the session;
    - legitimate owners keep full access.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(email="owner@test.bg", password="StrongPass123!")
        cls.attacker = UserModel.objects.create_user(email="attacker@test.bg", password="StrongPass123!")
        cls.house = House.objects.create(
            town="Sofia",
            address="Test str. 1",
            entrance="A",
            money_balance=Decimal("0.00"),
            user=cls.owner,
        )

    def test_house_detail_forbidden_for_non_owner_and_session_not_primed(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse("details_house", kwargs={"house_pk": self.house.pk}))

        self.assertEqual(response.status_code, 404)
        # Regression: the session must NOT be primed with the foreign house.
        self.assertIsNone(self.client.session.get("selected_house"))

    def test_owner_can_access_house_detail(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("details_house", kwargs={"house_pk": self.house.pk}))

        self.assertEqual(response.status_code, 200)

    def test_house_edit_forbidden_for_non_owner(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse("edit_house", kwargs={"house_pk": self.house.pk}))

        self.assertEqual(response.status_code, 404)

    def test_house_clients_list_forbidden_for_non_owner(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse("house_clients_list", kwargs={"house_pk": self.house.pk}))

        self.assertEqual(response.status_code, 404)


class HouseSignatureOptionTests(TestCase):
    """
    The per-house "Require signature on bills" option: checked by default
    (the pre-existing workflow), editable from the Edit House page.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(
            email="owner@test.bg", password="StrongPass123!")
        cls.house = House.objects.create(
            town="Sofia",
            address="Test str. 1",
            entrance="A",
            money_balance=Decimal("0.00"),
            user=cls.owner,
        )

    def test_new_house_defaults_to_signature_required(self):
        self.assertTrue(self.house.signature_required)

    def test_edit_page_renders_the_option_checked_by_default(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("edit_house", kwargs={"house_pk": self.house.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="signature_required"')
        self.assertContains(response, "checked")

    def test_edit_house_can_disable_and_reenable_signatures(self):
        self.client.force_login(self.owner)
        url = reverse("edit_house", kwargs={"house_pk": self.house.pk})
        data = {"town": "Sofia", "address": "Test str. 1",
                "entrance": "A", "money_balance": "0.00"}

        # The checkbox left unchecked opts the house out of signatures.
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.house.refresh_from_db()
        self.assertFalse(self.house.signature_required)

        # Ticking it again restores the default workflow.
        response = self.client.post(url, {**data, "signature_required": "on"})

        self.assertEqual(response.status_code, 302)
        self.house.refresh_from_db()
        self.assertTrue(self.house.signature_required)


class ClientsFloorFilterTests(TestCase):
    """
    The clients page filters by a typed floor number (?floor=N): anything
    that is not a non-negative integer means "no filter"; the filter
    composes with the existing payment-status filter; HTMX requests get
    only the results fragment.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(
            email="owner@test.bg", password="StrongPass123!")
        cls.house = House.objects.create(
            town="Sofia", address="Test str. 1", entrance="A",
            money_balance=Decimal("0.00"), user=cls.owner)

        cls.client_f1 = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=cls.house, user=cls.owner)
        cls.client_f2 = Client.objects.create(
            family_name="Petrov", floor=2, apartment="5",
            number_of_people=3, house=cls.house, user=cls.owner)
        cls.client_f2b = Client.objects.create(
            family_name="Georgiev", floor=2, apartment="6",
            number_of_people=2, house=cls.house, user=cls.owner)

    def test_floor_filters_the_list(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "house_clients_list", kwargs={"house_pk": self.house.pk}), {"floor": "2"})

        self.assertEqual(response.status_code, 200)
        clients = list(response.context["clients"])
        self.assertEqual(
            [c.family_name for c in clients], ["Petrov", "Georgiev"])
        self.assertEqual(response.context["selected_floor"], 2)
        self.assertContains(response, "Clients on floor 2")

    def test_non_numeric_floor_is_ignored(self):
        self.client.force_login(self.owner)

        for raw in ["abc", "-2", "1.5"]:
            response = self.client.get(reverse(
                "house_clients_list", kwargs={"house_pk": self.house.pk}), {"floor": raw})

            self.assertEqual(response.status_code, 200, raw)
            self.assertEqual(len(response.context["clients"]), 3, raw)
            self.assertIsNone(response.context["selected_floor"], raw)

    def test_impossible_floor_shows_no_clients(self):
        # A well-formed but absurd floor number is a real filter that
        # simply matches nothing.
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "house_clients_list", kwargs={"house_pk": self.house.pk}),
            {"floor": "999999999999999999999"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["clients"]), 0)
        self.assertContains(response, "No clients")

    def test_missing_floor_shows_all_clients(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "house_clients_list", kwargs={"house_pk": self.house.pk}), {"floor": ""})

        self.assertEqual(len(response.context["clients"]), 3)

    def test_floor_composes_with_payment_status_filter(self):
        ClientMonthlyBill.objects.create(
            month="01", year="2026",
            electricity_common=Decimal("100.00"),
            electricity_lift=Decimal("0.00"), internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"), fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"), fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"), others=Decimal("0.00"),
            amount_old_debts=Decimal("0.00"),
            house=self.house, client=self.client_f2, user=self.owner)

        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "house_clients_list", kwargs={"house_pk": self.house.pk}),
            {"floor": "2", "is_paid": "False"})

        self.assertEqual(
            [c.family_name for c in response.context["clients"]], ["Petrov"])
        self.assertContains(response, "Clients with unpaid bills")

    def test_htmx_request_returns_results_fragment_only(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "house_clients_list", kwargs={"house_pk": self.house.pk}),
            {"floor": "2"}, headers={"HX-Request": "true"})

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('id="clients-results"', html)
        self.assertNotIn("<html", html)

    def test_floor_filter_blocked_for_other_user(self):
        attacker = UserModel.objects.create_user(
            email="attacker@test.bg", password="StrongPass123!")
        self.client.force_login(attacker)

        response = self.client.get(reverse(
            "house_clients_list", kwargs={"house_pk": self.house.pk}), {"floor": "2"})

        self.assertEqual(response.status_code, 404)


class ClientsYearFilterTests(TestCase):
    """
    The clients page year filter (?year=YYYY) shows only clients with a
    bill in that year. It composes with the floor, month and payment-status
    filters, and all bill facets must match the same bill.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(
            email="owner@test.bg", password="StrongPass123!")
        cls.house = House.objects.create(
            town="Sofia", address="Test str. 1", entrance="A",
            money_balance=Decimal("0.00"), user=cls.owner)

        cls.client_2026 = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=cls.house, user=cls.owner)
        cls.client_2025 = Client.objects.create(
            family_name="Petrov", floor=2, apartment="5",
            number_of_people=3, house=cls.house, user=cls.owner)
        cls.client_without_bills = Client.objects.create(
            family_name="Georgiev", floor=2, apartment="6",
            number_of_people=2, house=cls.house, user=cls.owner)

        cls._create_monthly_bill(cls.client_2026, "01", "2026", is_paid=False)
        cls._create_monthly_bill(cls.client_2025, "01", "2025", is_paid=True)

    @classmethod
    def _create_monthly_bill(cls, client, month, year, is_paid):
        return ClientMonthlyBill.objects.create(
            month=month, year=year,
            electricity_common=Decimal("100.00"),
            electricity_lift=Decimal("0.00"), internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"), fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"), fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"), others=Decimal("0.00"),
            amount_old_debts=Decimal("0.00"), is_paid=is_paid,
            house=cls.house, client=client, user=cls.owner)

    def _get_clients(self, **params):
        return self.client.get(
            reverse("house_clients_list", kwargs={"house_pk": self.house.pk}),
            params)

    def test_year_filters_clients_with_bills_in_that_year(self):
        self.client.force_login(self.owner)

        response = self._get_clients(year="2026")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [c.family_name for c in response.context["clients"]], ["Ivanov"])
        self.assertEqual(response.context["selected_year"], "2026")
        self.assertContains(response, "Clients with bills in 2026")

    def test_malformed_year_is_ignored(self):
        self.client.force_login(self.owner)

        for raw in ["26", "abcd", "2026-01", ""]:
            response = self._get_clients(year=raw)

            self.assertEqual(response.status_code, 200, raw)
            self.assertEqual(len(response.context["clients"]), 3, raw)
            self.assertIsNone(response.context["selected_year"], raw)

    def test_year_composes_with_payment_status(self):
        self.client.force_login(self.owner)

        response = self._get_clients(year="2026", is_paid="False")

        self.assertEqual(
            [c.family_name for c in response.context["clients"]], ["Ivanov"])
        self.assertContains(response, "Clients with unpaid bills")

        response = self._get_clients(year="2025", is_paid="False")

        self.assertEqual(response.context["clients"].count(), 0)

    def test_month_and_year_must_match_the_same_bill(self):
        # Both clients have a January bill, but in different years: the
        # month filter must not borrow a bill from the other year.
        self.client.force_login(self.owner)

        response = self._get_clients(month="01", year="2026")

        self.assertEqual(
            [c.family_name for c in response.context["clients"]], ["Ivanov"])

    def test_year_composes_with_floor_filter(self):
        self.client.force_login(self.owner)

        response = self._get_clients(year="2026", floor="2")

        self.assertEqual(response.context["clients"].count(), 0)
        self.assertContains(response, "Clients on floor 2")
        self.assertContains(response, "Clients with bills in 2026")

    def test_year_filter_blocked_for_other_user(self):
        attacker = UserModel.objects.create_user(
            email="attacker@test.bg", password="StrongPass123!")
        self.client.force_login(attacker)

        response = self._get_clients(year="2026")

        self.assertEqual(response.status_code, 404)
