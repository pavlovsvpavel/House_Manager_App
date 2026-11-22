import re
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.clients.models import Client
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.houses.models import House
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill

UserModel = get_user_model()


def monthly_bill_payload(**overrides):
    """The full field set the fixed-taxes edit modal submits: the nine
    expense fields plus (optionally) the paid switch."""
    payload = {
        "electricity_common": "100.00",
        "electricity_lift": "0",
        "internet": "0",
        "maintenance_lift": "0",
        "fee_cleaner": "0",
        "fee_manager": "0",
        "fee_cashier": "0",
        "repairs": "0",
        "others": "0",
    }
    payload.update(overrides)
    return payload


class HouseBillsSecurityTests(TestCase):
    """
    Regression tests for the Phase 0 + Redesign Phase 1 security model:
    - house bills are always addressed as /houses/<house_pk>/bills/... and
      the house in the URL must belong to the logged-in user (IDOR);
    - the session-based "selected house" is no longer consulted anywhere;
    - marking a bill paid is idempotent (no balance changes on replay).
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
            fixed_monthly_taxes=True,
            user=cls.owner,
        )

        cls.monthly_bill = HouseMonthlyBill.objects.create(
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
            house=cls.house,
            user=cls.owner,
        )

        cls.other_bill = HouseOtherBill.objects.create(
            month="01", year="2026",
            comment="Elevator repair",
            total_amount=Decimal("50.00"),
            type_of_bill="Single bill",
            house=cls.house,
            user=cls.owner,
        )

    # --- IDOR: edit house bills -------------------------------------------

    def test_edit_monthly_bill_get_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse(
            "edit_house_bills", kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}))

        self.assertEqual(response.status_code, 404)
        self.monthly_bill.refresh_from_db()
        self.assertFalse(self.monthly_bill.is_paid)

    def test_edit_monthly_bill_post_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.post(
            reverse("edit_house_bills", kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}),
            {"is_paid": "on"},
        )

        self.assertEqual(response.status_code, 404)
        self.monthly_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.monthly_bill.is_paid)
        # Regression: the balance must not change via a foreign user's POST.
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_edit_other_bill_post_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.post(
            reverse("edit_other_house_bills", kwargs={"house_pk": self.house.pk, "pk": self.other_bill.pk}),
            {"is_paid": "on"},
        )

        self.assertEqual(response.status_code, 404)
        self.other_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.other_bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_list_house_bills_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse("list_house_bills", kwargs={"house_pk": self.house.pk}))

        self.assertEqual(response.status_code, 404)

    # --- Idempotency: replay must not re-debit the balance -----------------

    def test_mark_other_bill_paid_credits_balance_once(self):
        self.client.force_login(self.owner)

        url = reverse(
            "edit_other_house_bills", kwargs={"house_pk": self.house.pk, "pk": self.other_bill.pk})
        response = self.client.post(url, {"is_paid": "on"})

        self.assertEqual(response.status_code, 302)
        self.other_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.other_bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("-50.00"))

        # Replay: re-submitting the same form must not change the balance.
        response = self.client.post(url, {"is_paid": "on"})
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("-50.00"))

    # --- Create: house in the URL must belong to the user ------------------

    def test_create_house_bill_blocked_in_foreign_house_url(self):
        self.client.force_login(self.attacker)

        response = self.client.post(
            reverse("create_house_bills", kwargs={"house_pk": self.house.pk}),
            {
                "month": "01",
                "year": "2026",
                "electricity_common": "10",
                "electricity_lift": "0",
                "internet": "0",
                "maintenance_lift": "0",
                "fee_cleaner": "0",
                "fee_manager": "0",
                "fee_cashier": "0",
                "repairs": "0",
                "others": "0",
            })

        self.assertEqual(response.status_code, 404)
        self.assertEqual(HouseMonthlyBill.objects.count(), 1)  # only the fixture bill

    def test_create_house_bill_allowed_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("create_house_bills", kwargs={"house_pk": self.house.pk}),
            {
                "month": "02",
                "year": "2026",
                "electricity_common": "10",
                "electricity_lift": "0",
                "internet": "0",
                "maintenance_lift": "0",
                "fee_cleaner": "0",
                "fee_manager": "0",
                "fee_cashier": "0",
                "repairs": "0",
                "others": "0",
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(
            "details_house", kwargs={"house_pk": self.house.pk}))
        self.assertEqual(HouseMonthlyBill.objects.count(), 2)

    # --- HTMX fragments (Phase 2) -------------------------------------------

    def test_monthly_bills_list_partial_for_htmx(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("list_house_bills", kwargs={"house_pk": self.house.pk}),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "house_bills/partials/monthly_bill_list.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'id="bills-region"')
        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')

    def test_other_bills_list_partial_for_htmx(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("list_other_house_bills", kwargs={"house_pk": self.house.pk}),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "house_bills/partials/other_bill_list.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, f'id="bill-row-{self.other_bill.pk}"')

    def test_list_partial_applies_payment_filter(self):
        self.client.force_login(self.owner)

        url = reverse("list_house_bills", kwargs={"house_pk": self.house.pk})
        response = self.client.get(
            f"{url}?is_paid=False&month=01", HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')

        response = self.client.get(
            f"{url}?is_paid=True&month=01", HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f'id="bill-row-{self.monthly_bill.pk}"')

    def test_list_filters_by_month_only(self):
        """Regression: the view filtered only when is_paid was in the URL, so
        choosing a month and applying showed every month's bills."""
        self.client.force_login(self.owner)

        february = HouseMonthlyBill.objects.create(
            month="02", year="2026",
            electricity_common=Decimal("10.00"),
            electricity_lift=Decimal("0.00"),
            internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"),
            fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"),
            fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"),
            others=Decimal("0.00"),
            house=self.house,
            user=self.owner,
            is_paid=True,
        )

        url = reverse("list_house_bills", kwargs={"house_pk": self.house.pk})

        response = self.client.get(f"{url}?month=01", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')
        self.assertNotContains(response, f'id="bill-row-{february.pk}"')

        response = self.client.get(f"{url}?month=02", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{february.pk}"')
        self.assertNotContains(response, f'id="bill-row-{self.monthly_bill.pk}"')

    def test_list_filters_by_year(self):
        """The Year chip group: ?year= narrows to that year alone and
        composes with the payment-status filter."""
        self.client.force_login(self.owner)

        last_year = HouseMonthlyBill.objects.create(
            month="01", year="2025",
            electricity_common=Decimal("10.00"),
            electricity_lift=Decimal("0.00"),
            internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"),
            fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"),
            fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"),
            others=Decimal("0.00"),
            house=self.house,
            user=self.owner,
        )

        url = reverse("list_house_bills", kwargs={"house_pk": self.house.pk})

        response = self.client.get(f"{url}?year=2026", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')
        self.assertNotContains(response, f'id="bill-row-{last_year.pk}"')

        # All years back when the All chip is on (year param empty).
        response = self.client.get(f"{url}?year=&month=&is_paid=", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')
        self.assertContains(response, f'id="bill-row-{last_year.pk}"')

        # Composed: unpaid 2025 only.
        response = self.client.get(f"{url}?year=2025&is_paid=False", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{last_year.pk}"')
        self.assertNotContains(response, f'id="bill-row-{self.monthly_bill.pk}"')

    def test_list_filters_by_payment_status_only(self):
        """Regression: the helper nested the is_paid branches under the month
        check, so debt filters with "All" months returned everything."""
        self.client.force_login(self.owner)

        paid_feb = HouseMonthlyBill.objects.create(
            month="02", year="2026",
            electricity_common=Decimal("10.00"),
            electricity_lift=Decimal("0.00"),
            internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"),
            fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"),
            fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"),
            others=Decimal("0.00"),
            house=self.house,
            user=self.owner,
            is_paid=True,
        )

        url = reverse("list_house_bills", kwargs={"house_pk": self.house.pk})

        response = self.client.get(f"{url}?is_paid=True", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{paid_feb.pk}"')
        self.assertNotContains(response, f'id="bill-row-{self.monthly_bill.pk}"')

        response = self.client.get(f"{url}?is_paid=False", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')
        self.assertNotContains(response, f'id="bill-row-{paid_feb.pk}"')

    def test_edit_bill_htmx_get_returns_modal_fragment(self):
        self.client.force_login(self.owner)
        url = reverse(
            "edit_house_bills",
            kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk})

        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "house_bills/partials/monthly_bill_modal.html")
        self.assertContains(response, "data-bill-modal")
        self.assertContains(response, f'hx-post="{url}"')
        self.assertNotContains(response, "<html")

    def test_edit_bill_htmx_post_swaps_row_and_triggers_event(self):
        self.client.force_login(self.owner)
        url = reverse(
            "edit_house_bills",
            kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk})

        response = self.client.post(
            url, monthly_bill_payload(is_paid="on"), HTTP_HX_REQUEST="true")

        # The row swaps in place and the summary line swaps out-of-band.
        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')
        self.assertContains(response, 'id="bills-summary"')
        self.assertContains(response, 'hx-swap-oob="true"')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "billPaid")
        self.assertTemplateUsed(
            response, "house_bills/partials/monthly_bill_row.html")
        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')
        self.assertNotContains(response, "<html")

        self.monthly_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.monthly_bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("-100.00"))

        # Replay through HTMX must stay idempotent and re-render the dialog
        # (with the error) instead of overwriting the paid row.
        response = self.client.post(
            url, {"is_paid": "on"}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(response["HX-Retarget"], "#bill-modal-container")

        # Idempotency under the row lock (#18): the replay must not debit
        # the balance a second time.
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("-100.00"))

        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("-100.00"))

    # --- Revert (undo payment) ----------------------------------------------

    def test_revert_monthly_bill_restores_balance(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse("edit_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}),
            monthly_bill_payload(is_paid="on"))
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("-100.00"))

        response = self.client.post(
            reverse("revert_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "billReverted")
        self.assertTemplateUsed(
            response, "house_bills/partials/monthly_bill_row.html")
        self.assertContains(response, f'id="bill-row-{self.monthly_bill.pk}"')
        self.assertContains(response, 'id="bills-summary"')
        self.assertNotContains(response, "<html")

        self.monthly_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.monthly_bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

        # Replay: reverting an already-unpaid bill must not touch the balance.
        self.client.post(
            reverse("revert_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}),
            HTTP_HX_REQUEST="true",
        )
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_revert_other_bill_restores_total_amount(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse("edit_other_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.other_bill.pk}),
            {"is_paid": "on"})
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("-50.00"))

        response = self.client.post(
            reverse("revert_other_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.other_bill.pk}),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.other_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.other_bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_revert_blocked_for_other_user(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse("edit_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}),
            monthly_bill_payload(is_paid="on"))

        self.client.force_login(self.attacker)
        response = self.client.post(
            reverse("revert_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}))

        self.assertEqual(response.status_code, 404)
        self.monthly_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.monthly_bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("-100.00"))

    def test_revert_without_htmx_redirects_to_list(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("revert_house_bills",
                    kwargs={"house_pk": self.house.pk, "pk": self.monthly_bill.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("list_house_bills", kwargs={"house_pk": self.house.pk}))


class ReportsMultiMonthTests(TestCase):
    """
    Report pages accept several months at once (<select multiple>): rows
    collapse to one per client with the money columns summed, the details
    card lists the months as numbers ("01, 02, 03"), and the Signature
    column (which cannot be summed) is replaced by Paid - "Yes" only when
    every selected month's bill for the client is paid.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(email="owner@test.bg", password="StrongPass123!")

        cls.house = House.objects.create(
            town="Sofia",
            address="Test str. 1",
            entrance="A",
            money_balance=Decimal("0.00"),
            user=cls.owner,
        )

        cls.client_a = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=cls.house, user=cls.owner)
        cls.client_b = Client.objects.create(
            family_name="Petrov", floor=2, apartment="2",
            number_of_people=3, house=cls.house, user=cls.owner)

        bill_defaults = dict(
            electricity_lift=Decimal("0.00"), internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"), fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"), fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"), others=Decimal("0.00"),
            house=cls.house, user=cls.owner)

        # Client A: January + February (one unpaid, one paid);
        # client B: February only (paid).
        cls.bill_a_jan = ClientMonthlyBill.objects.create(
            month="01", year="2026",
            electricity_common=Decimal("100.00"), amount_old_debts=Decimal("10.00"),
            client=cls.client_a, is_paid=False, **bill_defaults)
        cls.bill_a_feb = ClientMonthlyBill.objects.create(
            month="02", year="2026",
            electricity_common=Decimal("110.00"), amount_old_debts=Decimal("0.00"),
            client=cls.client_a, is_paid=True, **bill_defaults)
        cls.bill_b_feb = ClientMonthlyBill.objects.create(
            month="02", year="2026",
            electricity_common=Decimal("50.00"), amount_old_debts=Decimal("0.00"),
            client=cls.client_b, is_paid=True, **bill_defaults)
        cls.bill_a_jan.refresh_from_db()
        cls.bill_a_feb.refresh_from_db()
        cls.bill_b_feb.refresh_from_db()

        cls.other_bill_feb = HouseOtherBill.objects.create(
            month="02", year="2026",
            comment="Elevator repair", total_amount=Decimal("50.00"),
            type_of_bill="Bill for all clients", house=cls.house, user=cls.owner)

    # --- monthly reports ----------------------------------------------------

    def test_monthly_report_multi_month_sums_per_client(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "reports_bills", kwargs={"house_pk": self.house.pk}),
            {"month": ["01", "02"], "year": "2026"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "01, 02")

        # One row per client: A summed 210.00 (100+110), B 50.00.
        clients_bills = response.context["clients_bills"]
        self.assertEqual(len(clients_bills), 2)
        row_a = next(r for r in clients_bills if r.client == self.client_a)
        row_b = next(r for r in clients_bills if r.client == self.client_b)
        self.assertEqual(row_a.total_amount, Decimal("210.00"))
        self.assertEqual(row_a.amount_old_debts, Decimal("10.00"))
        self.assertEqual(row_b.total_amount, Decimal("50.00"))

        # Table foot sums over both months.
        self.assertEqual(response.context["clients_bills_total_amount"], Decimal("260.00"))
        self.assertEqual(response.context["unpaid_bills"], Decimal("10.00"))
        self.assertEqual(response.context["amount_for_collection"], Decimal("270.00"))

    def test_monthly_report_multi_month_swaps_signature_for_paid(self):
        # The house requires signatures (default), but a signature cannot be
        # summed: multi-month shows Paid instead - "Yes" only when every
        # selected month is paid (A: Jan unpaid -> No; B: both months paid).
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "reports_bills", kwargs={"house_pk": self.house.pk}),
            {"month": ["01", "02"], "year": "2026"})

        self.assertContains(response, "Paid")
        self.assertNotContains(response, "Signature")
        rows_by_client = {row.client.pk: row for row in response.context["clients_bills"]}
        self.assertFalse(rows_by_client[self.client_a.pk].is_paid)
        self.assertTrue(rows_by_client[self.client_b.pk].is_paid)

    def test_monthly_report_single_month_keeps_signature_column(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "reports_bills", kwargs={"house_pk": self.house.pk}),
            {"month": ["01"], "year": "2026"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Signature")
        self.assertNotContains(response, "Paid")
        # Months render as numbers, also for a single selection.
        self.assertContains(response, "01")

    def test_month_picker_checkboxes_persist_selection(self):
        # The month picker is a checkbox grid: the picked months render
        # checked after a search (no ctrl+click needed, no JS involved).
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "reports_bills", kwargs={"house_pk": self.house.pk}),
            {"month": ["01", "02"], "year": "2026"})

        html = response.content.decode()
        checked = re.findall(
            r'<input type="checkbox" name="month" value="(\d\d)"\s+checked>', html)
        self.assertEqual(sorted(checked), ["01", "02"])

        # The picked months stay checked; the year radio stays checked.
        self.assertContains(response, "01, 02")
        self.assertTrue(re.search(r'name="year" value="2026"\s+checked', html))

    def test_monthly_report_without_month_shows_no_table(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "reports_bills", kwargs={"house_pk": self.house.pk}), {"year": "2026"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["clients_bills"]), 0)

    # --- other-bills reports -------------------------------------------------

    def test_other_bills_report_multi_month_sums_per_client(self):
        ClientOtherBill.objects.create(
            month="01", year="2026", comment="Roof fund",
            total_amount=Decimal("30.00"),
            house=self.house, client=self.client_a, user=self.owner)
        ClientOtherBill.objects.create(
            month="02", year="2026", comment="Roof fund",
            total_amount=Decimal("20.00"),
            house=self.house, client=self.client_a, user=self.owner)

        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "reports_other_bills", kwargs={"house_pk": self.house.pk}),
            {"month": ["01", "02"], "year": "2026",
             "type_of_bill": "Bill for all clients"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "01, 02")

        row_a = next(r for r in response.context["clients_bills"] if r.client == self.client_a)
        self.assertEqual(row_a.total_amount, Decimal("50.00"))
        self.assertEqual(response.context["clients_bills_total_amount"], Decimal("50.00"))
        self.assertNotContains(response, "Signature")

    def test_other_bills_report_single_type_sums_total(self):
        HouseOtherBill.objects.create(
            month="01", year="2026", comment="Elevator repair",
            total_amount=Decimal("40.00"), type_of_bill="Single bill",
            house=self.house, user=self.owner)
        HouseOtherBill.objects.create(
            month="02", year="2026", comment="Elevator repair",
            total_amount=Decimal("50.00"), type_of_bill="Single bill",
            house=self.house, user=self.owner)

        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "reports_other_bills", kwargs={"house_pk": self.house.pk}),
            {"month": ["01", "02"], "year": "2026", "type_of_bill": "Single bill"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "01, 02")
        # One row per bill (comments differ), total summed over the months.
        self.assertEqual(len(response.context["single_bills"]), 2)
        self.assertEqual(response.context["calculated_total_amount"], Decimal("90.00"))

        # Single bills carry no client: the table has no name column, the
        # comment leads (left-aligned as the first column).
        self.assertNotContains(response, "Full name")
        self.assertContains(response, "<th>Comment</th>")

    def test_reports_blocked_for_other_user(self):
        attacker = UserModel.objects.create_user(
            email="attacker@test.bg", password="StrongPass123!")
        self.client.force_login(attacker)

        response = self.client.get(reverse(
            "reports_bills", kwargs={"house_pk": self.house.pk}),
            {"month": ["01", "02"], "year": "2026"})

        self.assertEqual(response.status_code, 404)


class HouseMonthlyBillAmountEditTests(TestCase):
    """
    A house monthly bill's amounts are editable only while the bill is
    unpaid AND the house has the "fixed monthly taxes" setting on: those
    house bills stand alone, while non-fixed houses distribute the amounts
    to the client bills at creation (calculate_fees) — editing them would
    desync the house bill from what the clients were charged. A paid bill
    is final: no edits, and payment replays stay no-ops.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(email="owner@test.bg", password="StrongPass123!")

        cls.fixed_house = House.objects.create(
            town="Sofia", address="Fixed str. 1", entrance="A",
            money_balance=Decimal("0.00"), fixed_monthly_taxes=True,
            user=cls.owner)
        cls.free_house = House.objects.create(
            town="Sofia", address="Free str. 1", entrance="A",
            money_balance=Decimal("0.00"), fixed_monthly_taxes=False,
            user=cls.owner)

        def make_bill(house):
            return HouseMonthlyBill.objects.create(
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
                house=house, user=cls.owner)

        cls.fixed_bill = make_bill(cls.fixed_house)
        cls.free_bill = make_bill(cls.free_house)

    def edit_url(self, bill):
        return reverse(
            "edit_house_bills", kwargs={"house_pk": bill.house_id, "pk": bill.pk})

    # --- modal rendering -----------------------------------------------------

    def test_fixed_house_modal_renders_amount_fields(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.edit_url(self.fixed_bill), HTTP_HX_REQUEST="true")

        self.assertContains(response, 'name="electricity_common"')
        self.assertContains(response, "data-bill-edit")

        # Editing is not paying: the Save button must be usable without
        # the paid switch (also for users without JavaScript).
        save_button = re.search(
            r'<button id="save-btn"[^>]*>', response.content.decode()).group(0)
        self.assertNotIn("disabled", save_button)

    def test_non_fixed_house_modal_keeps_payment_only_form(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.edit_url(self.free_bill), HTTP_HX_REQUEST="true")

        self.assertNotContains(response, 'name="electricity_common"')
        self.assertNotContains(response, "data-bill-edit")
        self.assertContains(response, 'name="is_paid"')

    # --- editing without paying ---------------------------------------------

    def test_fixed_house_amount_edit_saves_without_paying(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.edit_url(self.fixed_bill),
            monthly_bill_payload(electricity_common="140.50", repairs="10"),
            HTTP_HX_REQUEST="true")

        # The row swaps in place with the fresh total; the modal closes
        # through the same billPaid trigger the payment flow uses (an
        # unpaid row carries no revert URL, so no toast is offered).
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'id="bill-row-{self.fixed_bill.pk}"')
        self.assertContains(response, 'id="bills-summary"')
        self.assertEqual(response["HX-Trigger"], "billPaid")

        self.fixed_bill.refresh_from_db()
        self.fixed_house.refresh_from_db()
        self.assertEqual(self.fixed_bill.electricity_common, Decimal("140.50"))
        self.assertEqual(self.fixed_bill.repairs, Decimal("10"))
        # The DB-generated total followed the corrected fields.
        self.assertEqual(self.fixed_bill.total_amount, Decimal("150.50"))
        self.assertFalse(self.fixed_bill.is_paid)
        # No payment, no balance movement.
        self.assertEqual(self.fixed_house.money_balance, Decimal("0.00"))

    def test_fixed_house_amount_edit_full_page_redirects(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.edit_url(self.fixed_bill), monthly_bill_payload(internet="5"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(
            "list_house_bills", kwargs={"house_pk": self.fixed_house.pk}))
        self.fixed_bill.refresh_from_db()
        self.assertEqual(self.fixed_bill.internet, Decimal("5"))
        self.assertFalse(self.fixed_bill.is_paid)

    # --- editing and paying in one submit ------------------------------------

    def test_fixed_house_edit_and_pay_debits_new_total(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.edit_url(self.fixed_bill),
            monthly_bill_payload(electricity_common="60", is_paid="on"))

        self.assertEqual(response.status_code, 302)
        self.fixed_bill.refresh_from_db()
        self.fixed_house.refresh_from_db()
        self.assertTrue(self.fixed_bill.is_paid)
        self.assertEqual(self.fixed_bill.total_amount, Decimal("60.00"))
        # The debit follows the corrected total, not the original one.
        self.assertEqual(self.fixed_house.money_balance, Decimal("-60.00"))

    # --- month/year stay fixed -------------------------------------------------

    def test_month_and_year_are_not_editable(self):
        self.client.force_login(self.owner)

        self.client.post(
            self.edit_url(self.fixed_bill),
            monthly_bill_payload(month="03", year="2027", electricity_common="55"))

        self.fixed_bill.refresh_from_db()
        self.assertEqual(self.fixed_bill.month, "01")
        self.assertEqual(self.fixed_bill.year, "2026")
        self.assertEqual(self.fixed_bill.electricity_common, Decimal("55"))

    # --- non-fixed houses: no editing ------------------------------------------

    def test_non_fixed_house_amounts_are_not_editable(self):
        self.client.force_login(self.owner)

        # The is_paid-only form ignores the posted amount fields, and a
        # submission without the paid switch stays an error.
        response = self.client.post(
            self.edit_url(self.free_bill),
            monthly_bill_payload(electricity_common="999"))

        self.assertEqual(response.status_code, 200)  # form re-rendered with errors
        self.free_bill.refresh_from_db()
        self.free_house.refresh_from_db()
        self.assertEqual(self.free_bill.electricity_common, Decimal("100.00"))
        self.assertFalse(self.free_bill.is_paid)
        self.assertEqual(self.free_house.money_balance, Decimal("0.00"))

    def test_non_fixed_house_payment_flow_unchanged(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.edit_url(self.free_bill), {"is_paid": "on"})

        self.assertEqual(response.status_code, 302)
        self.free_bill.refresh_from_db()
        self.free_house.refresh_from_db()
        self.assertTrue(self.free_bill.is_paid)
        self.assertEqual(self.free_house.money_balance, Decimal("-100.00"))

    # --- paid bills are final --------------------------------------------------

    def test_paid_fixed_bill_cannot_be_edited_or_repaid(self):
        self.client.force_login(self.owner)
        self.client.post(
            self.edit_url(self.fixed_bill), monthly_bill_payload(is_paid="on"))
        self.fixed_house.refresh_from_db()
        self.assertEqual(self.fixed_house.money_balance, Decimal("-100.00"))

        # Replay with corrected amounts: the idempotency guard keeps the
        # amounts and the balance untouched.
        response = self.client.post(
            self.edit_url(self.fixed_bill),
            monthly_bill_payload(electricity_common="777"))

        self.assertEqual(response.status_code, 200)
        self.fixed_bill.refresh_from_db()
        self.fixed_house.refresh_from_db()
        self.assertEqual(self.fixed_bill.electricity_common, Decimal("100.00"))
        self.assertEqual(self.fixed_house.money_balance, Decimal("-100.00"))
