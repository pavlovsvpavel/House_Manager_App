from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.clients.models import Client
from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.houses.models import House

UserModel = get_user_model()


class ClientBillsSecurityTests(TestCase):
    """
    Regression tests for the Phase 0 + Redesign Phase 1 security model:
    - client bills are always addressed as
      /houses/<house_pk>/clients/<client_pk>/... and both the house and the
      client in the URL must belong to the logged-in user (IDOR);
    - the session-based "selected client/house" is no longer consulted;
    - receipt download is restricted to the bill's owner;
    - marking a client bill paid is idempotent (no balance changes on
      replay).
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

        cls.client_obj = Client.objects.create(
            family_name="Ivanov",
            floor=1,
            apartment="1",
            number_of_people=2,
            house=cls.house,
            user=cls.owner,
        )

        cls.bill = ClientMonthlyBill.objects.create(
            month="01", year="2026",
            electricity_common=Decimal("100.00"),
            electricity_lift=Decimal("0.00"),
            internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"),
            fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"),
            fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"),
            others=Decimal("0.00"),
            amount_old_debts=Decimal("0.00"),
            house=cls.house,
            client=cls.client_obj,
            user=cls.owner,
        )

    # --- IDOR: client bill lists -------------------------------------------

    def test_client_bills_list_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse(
            "list_client_bills",
            kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 404)

    # --- IDOR: client bill edit (GET and POST) ------------------------------

    def test_edit_client_bill_get_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse(
            "edit_client_bill",
            kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk, "pk": self.bill.pk}))

        self.assertEqual(response.status_code, 404)

    def test_edit_client_bill_post_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.post(
            reverse("edit_client_bill",
                    kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk, "pk": self.bill.pk}),
            {"is_paid": "on"},
        )

        self.assertEqual(response.status_code, 404)
        self.bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.bill.is_paid)
        # Regression: the balance must not change via a foreign user's POST.
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_edit_client_bill_post_blocked_for_foreign_client_pk(self):
        """Same house, same owner, but the bill belongs to another client —
        the client_pk in the URL must match the bill's client."""
        self.client.force_login(self.owner)

        other_client = Client.objects.create(
            family_name="Petrov",
            floor=2,
            apartment="2",
            number_of_people=1,
            house=self.house,
            user=self.owner,
        )

        response = self.client.post(
            reverse("edit_client_bill",
                    kwargs={"house_pk": self.house.pk, "client_pk": other_client.pk, "pk": self.bill.pk}),
            {"is_paid": "on"},
        )

        self.assertEqual(response.status_code, 404)
        self.bill.refresh_from_db()
        self.assertFalse(self.bill.is_paid)

    # --- Owner renders: template URL reversals must not 500 -----------------

    def test_client_bills_list_renders_for_owner(self):
        """Regression: the list template reversed 'details_client' with
        client_pk (route uses pk) and 500'd for the owner."""
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "list_client_bills",
            kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ivanov")

    def test_client_other_bills_list_renders_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "list_other_client_bills",
            kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 200)

    # --- Receipt download (IDOR) --------------------------------------------

    def test_receipt_download_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse(
            "download_receipt",
            kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk, "pk": self.bill.pk}))

        self.assertEqual(response.status_code, 404)

    def test_receipt_download_allowed_for_owner(self):
        self.client.force_login(self.owner)
        self.bill.is_paid = True
        self.bill.save()

        response = self.client.get(reverse(
            "download_receipt",
            kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk, "pk": self.bill.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    # --- Idempotency: replay must not re-credit the balance ------------------

    def test_mark_client_bill_paid_credits_balance_once(self):
        self.client.force_login(self.owner)

        url = reverse(
            "edit_client_bill",
            kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk, "pk": self.bill.pk})
        response = self.client.post(url, {"is_paid": "on"})

        self.assertEqual(response.status_code, 302)
        self.bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("100.00"))

        # Replay: re-submitting the same form must not change the balance.
        response = self.client.post(url, {"is_paid": "on"})
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("100.00"))
