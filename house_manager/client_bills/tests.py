import base64
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.clients.models import Client
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.house_bills.models import HouseOtherBill
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

    # --- Revert (undo payment) ----------------------------------------------

    def test_revert_client_bill_restores_balance_and_clears_signature(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse("edit_client_bill",
                    kwargs={"house_pk": self.house.pk,
                            "client_pk": self.client_obj.pk,
                            "pk": self.bill.pk}),
            {"is_paid": "on", "signature": "PHN2Zy8+"})
        self.bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("100.00"))

        response = self.client.post(
            reverse("revert_client_bill",
                    kwargs={"house_pk": self.house.pk,
                            "client_pk": self.client_obj.pk,
                            "pk": self.bill.pk}),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "billReverted")
        self.assertTemplateUsed(
            response, "client_bills/partials/monthly_bill_row.html")
        self.assertContains(response, f'id="bill-row-{self.bill.pk}"')
        self.assertNotContains(response, "<html")

        self.bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.bill.is_paid)
        self.assertEqual(self.bill.signature, "")
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

        # Replay: reverting an already-unpaid bill must not touch the balance.
        self.client.post(
            reverse("revert_client_bill",
                    kwargs={"house_pk": self.house.pk,
                            "client_pk": self.client_obj.pk,
                            "pk": self.bill.pk}),
            HTTP_HX_REQUEST="true",
        )
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_revert_client_bill_blocked_for_foreign_client_pk(self):
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
            reverse("revert_client_bill",
                    kwargs={"house_pk": self.house.pk,
                            "client_pk": other_client.pk,
                            "pk": self.bill.pk}))

        self.assertEqual(response.status_code, 404)
        self.bill.refresh_from_db()
        self.assertFalse(self.bill.is_paid)

    def test_revert_client_bill_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.post(
            reverse("revert_client_bill",
                    kwargs={"house_pk": self.house.pk,
                            "client_pk": self.client_obj.pk,
                            "pk": self.bill.pk}))

        self.assertEqual(response.status_code, 404)
        self.bill.refresh_from_db()
        self.assertFalse(self.bill.is_paid)

    # --- HTMX fragments (Phase 2) -------------------------------------------

    def test_client_bills_list_partial_for_htmx(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("list_client_bills",
                    kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk}),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "client_bills/partials/monthly_bill_list.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'id="bills-region"')
        self.assertContains(response, f'id="bill-row-{self.bill.pk}"')

    def test_client_other_bills_list_partial_for_htmx(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("list_other_client_bills",
                    kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk}),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "client_bills/partials/other_bill_list.html")
        self.assertNotContains(response, "<html")

    def test_client_bills_list_filters_by_month_and_status(self):
        """Regression: month-only queries never filtered (the view gated on
        is_paid), and is_paid-only queries leaked all months (the helper
        nested its branches under the month check)."""
        self.client.force_login(self.owner)

        paid_feb = ClientMonthlyBill.objects.create(
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
            amount_old_debts=Decimal("0.00"),
            house=self.house,
            client=self.client_obj,
            user=self.owner,
            is_paid=True,
        )

        url = reverse("list_client_bills",
                      kwargs={"house_pk": self.house.pk, "client_pk": self.client_obj.pk})

        # Month only: January shows its bill, not February's.
        response = self.client.get(f"{url}?month=01", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.bill.pk}"')
        self.assertNotContains(response, f'id="bill-row-{paid_feb.pk}"')

        # Payment status only ("All" months): debts vs paid.
        response = self.client.get(f"{url}?is_paid=True", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{paid_feb.pk}"')
        self.assertNotContains(response, f'id="bill-row-{self.bill.pk}"')

        response = self.client.get(f"{url}?is_paid=False", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.bill.pk}"')
        self.assertNotContains(response, f'id="bill-row-{paid_feb.pk}"')

        # Both together.
        response = self.client.get(
            f"{url}?is_paid=False&month=01", HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.bill.pk}"')
        self.assertNotContains(response, f'id="bill-row-{paid_feb.pk}"')

    def test_edit_client_bill_htmx_get_returns_modal_with_signature_pad(self):
        self.client.force_login(self.owner)
        url = reverse(
            "edit_client_bill",
            kwargs={"house_pk": self.house.pk,
                    "client_pk": self.client_obj.pk,
                    "pk": self.bill.pk})

        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "client_bills/partials/monthly_bill_modal.html")
        self.assertContains(response, "data-bill-modal")
        self.assertContains(response, 'id="signature"')
        self.assertContains(response, f'hx-post="{url}"')
        self.assertNotContains(response, "<html")

    def test_edit_client_bill_htmx_post_swaps_row_and_credits_once(self):
        self.client.force_login(self.owner)
        url = reverse(
            "edit_client_bill",
            kwargs={"house_pk": self.house.pk,
                    "client_pk": self.client_obj.pk,
                    "pk": self.bill.pk})

        response = self.client.post(
            url,
            {"is_paid": "on", "signature": "PHN2Zy8+"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "billPaid")
        self.assertTemplateUsed(
            response, "client_bills/partials/monthly_bill_row.html")
        self.assertContains(response, f'id="bill-row-{self.bill.pk}"')
        self.assertNotContains(response, "<html")

        self.bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.bill.is_paid)
        self.assertEqual(
            self.bill.signature, "data:image/svg+xml;base64,PHN2Zy8+")
        self.assertEqual(self.house.money_balance, Decimal("100.00"))

        # Replay: stays idempotent and keeps the dialog target for the error.
        response = self.client.post(
            url,
            {"is_paid": "on", "signature": "PHN2Zy8+"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(response["HX-Retarget"], "#bill-modal-container")

        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("100.00"))


class ClientBillMultiPaymentTests(TestCase):
    """
    Multi-payment: the payment modal may check other unpaid bills of the
    same client; they are paid (or reverted) in ONE transaction — one
    signature on every selected bill, one locked balance update.
    """
    SIGNATURE_B64 = "data:image/svg+xml;base64,PHN2Zy8+"

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(
            email="owner@test.bg", password="StrongPass123!")
        cls.attacker = UserModel.objects.create_user(
            email="attacker@test.bg", password="StrongPass123!")

        cls.house = House.objects.create(
            town="Sofia", address="Test str. 1", entrance="A",
            money_balance=Decimal("0.00"), user=cls.owner)

        cls.client_obj = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=cls.house, user=cls.owner)

        cls.other_client = Client.objects.create(
            family_name="Petrov", floor=2, apartment="2",
            number_of_people=2, house=cls.house, user=cls.owner)

        def make_bill(month, electricity):
            return ClientMonthlyBill.objects.create(
                month=month, year="2026",
                electricity_common=Decimal(electricity),
                electricity_lift=Decimal("0.00"),
                internet=Decimal("0.00"),
                maintenance_lift=Decimal("0.00"),
                fee_cleaner=Decimal("0.00"),
                fee_manager=Decimal("0.00"),
                fee_cashier=Decimal("0.00"),
                repairs=Decimal("0.00"),
                others=Decimal("0.00"),
                amount_old_debts=Decimal("0.00"),
                house=cls.house, client=cls.client_obj, user=cls.owner)

        # Jan = the bill being paid in the modal; Feb + Mar = group targets.
        cls.bill_jan = make_bill("01", "100.00")   # total 100.00
        cls.bill_feb = make_bill("02", "50.00")    # total 50.00
        cls.bill_mar = make_bill("03", "30.00")    # total 30.00

        cls.bill_paid = make_bill("04", "7.00")    # total 7.00, already paid
        cls.bill_paid.is_paid = True
        cls.bill_paid.signature = cls.SIGNATURE_B64
        cls.bill_paid.save()

        cls.foreign_bill = ClientMonthlyBill.objects.create(
            month="01", year="2026",
            electricity_common=Decimal("99.00"),
            electricity_lift=Decimal("0.00"),
            internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"),
            fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"),
            fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"),
            others=Decimal("0.00"),
            amount_old_debts=Decimal("0.00"),
            house=cls.house, client=cls.other_client, user=cls.owner)
        # Paid — a forged revert id must not undo another client's payment.
        cls.foreign_bill.is_paid = True
        cls.foreign_bill.signature = cls.SIGNATURE_B64
        cls.foreign_bill.save()

    def pay_url(self, bill):
        return reverse("edit_client_bill", kwargs={
            "house_pk": self.house.pk,
            "client_pk": self.client_obj.pk,
            "pk": bill.pk})

    def test_payment_modal_lists_other_unpaid_bills(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            self.pay_url(self.bill_jan), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        # Jan's modal offers Feb, Mar and the already-paid Apr? No — only unpaid.
        self.assertContains(response, 'name="pay_bill"')
        self.assertContains(response, f'value="{self.bill_feb.pk}"')
        self.assertContains(response, f'value="{self.bill_mar.pk}"')
        self.assertNotContains(response, f'value="{self.bill_paid.pk}"')
        self.assertNotContains(response, f'value="{self.foreign_bill.pk}"')

    def test_summary_oob_swaps_after_multi_pay(self):
        # The response carries an out-of-band summary line reflecting the
        # fresh state: after paying Jan+Feb+Mar the client has no unpaid
        # bills, and the summary swaps without a page reload.
        self.client.force_login(self.owner)

        response = self.client.post(
            self.pay_url(self.bill_jan),
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(self.bill_feb.pk), str(self.bill_mar.pk)]},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="bills-summary"', content)
        summary_fragment = content.split('id="bills-summary"')[1]
        self.assertIn(">0<", summary_fragment)  # Unpaid count is now zero

    def test_summary_oob_respects_the_page_filter(self):
        # The payment form's action carries the list's query string, so
        # the summary recomputes the FILTERED view: with ?is_paid=False
        # the whole filtered set was just paid, and the summary reflects
        # that (count 0), not the unfiltered totals.
        self.client.force_login(self.owner)

        response = self.client.post(
            self.pay_url(self.bill_jan) + "?is_paid=False",
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(self.bill_feb.pk), str(self.bill_mar.pk)]},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="bills-summary"', content)
        self.assertIn("Unpaid", content)

    def test_undo_response_swaps_summary_oob(self):
        self.client.force_login(self.owner)

        # Pay everything first.
        self.bill_jan.is_paid = True
        self.bill_jan.signature = self.SIGNATURE_B64
        self.bill_jan.save()
        self.bill_feb.is_paid = True
        self.bill_feb.signature = self.SIGNATURE_B64
        self.bill_feb.save()

        response = self.client.post(
            reverse("revert_client_bill", kwargs={
                "house_pk": self.house.pk,
                "client_pk": self.client_obj.pk,
                "pk": self.bill_jan.pk}),
            {"paid_together": str(self.bill_feb.pk)},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "billReverted")
        self.assertContains(response, 'id="bills-summary"')

    def test_paid_bill_modal_is_read_only_receipt(self):
        # A paid bill's modal must not offer the group-pay checkboxes or the
        # paid switch: every POST on an already-paid bill is rejected by the
        # idempotency guard, so those controls would be dead UI. It renders
        # as a receipt instead (signature + download link).
        self.client.force_login(self.owner)

        response = self.client.get(
            self.pay_url(self.bill_paid), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="pay_bill"')
        self.assertNotContains(response, 'name="is_paid"')
        self.assertContains(response, "/receipt/download/")
        self.assertContains(response, self.SIGNATURE_B64)

    def test_multi_pay_marks_all_selected_paid_with_one_signature_and_credit(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.pay_url(self.bill_jan),
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(self.bill_feb.pk), str(self.bill_mar.pk)]},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "billPaid")
        self.assertEqual(response["X-Paid-Together"],
                         f"{self.bill_feb.pk},{self.bill_mar.pk}")
        # Main row + one OOB fragment per group bill + one OOB summary line.
        self.assertEqual(response.content.decode().count("hx-swap-oob"), 3)
        self.assertContains(response, 'id="bills-summary"')
        self.assertContains(response, 'hx-swap-oob="true"')

        for bill in (self.bill_jan, self.bill_feb, self.bill_mar):
            bill.refresh_from_db()
            self.assertTrue(bill.is_paid)
            self.assertEqual(bill.signature, self.SIGNATURE_B64)

        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("180.00"))

    def test_multi_pay_skips_already_paid_and_foreign_bills(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.pay_url(self.bill_jan),
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(self.bill_feb.pk), str(self.bill_paid.pk),
                          str(self.foreign_bill.pk)]},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        # Only Feb joins the group — the already-paid and the other
        # client's bill are silently dropped.
        self.assertEqual(response["X-Paid-Together"], str(self.bill_feb.pk))
        # Feb's OOB row + the OOB summary line.
        self.assertEqual(response.content.decode().count("hx-swap-oob"), 2)

        self.bill_paid.refresh_from_db()
        self.foreign_bill.refresh_from_db()
        self.bill_feb.refresh_from_db()
        self.assertTrue(self.bill_paid.is_paid)
        # The other client's bill is untouched — not credited, not modified.
        self.assertTrue(self.foreign_bill.is_paid)
        self.assertEqual(self.foreign_bill.signature, self.SIGNATURE_B64)
        self.assertTrue(self.bill_feb.is_paid)

        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("150.00"))

    def test_undo_reverts_whole_group(self):
        self.client.force_login(self.owner)
        self.client.post(
            self.pay_url(self.bill_jan),
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(self.bill_feb.pk), str(self.bill_mar.pk)]})
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("180.00"))

        response = self.client.post(
            reverse("revert_client_bill", kwargs={
                "house_pk": self.house.pk,
                "client_pk": self.client_obj.pk,
                "pk": self.bill_jan.pk}),
            {"paid_together": [str(self.bill_feb.pk), str(self.bill_mar.pk)]},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Trigger"], "billReverted")
        # Two group rows back to unpaid + one OOB summary line.
        self.assertEqual(response.content.decode().count("hx-swap-oob"), 3)

        for bill in (self.bill_jan, self.bill_feb, self.bill_mar):
            bill.refresh_from_db()
            self.assertFalse(bill.is_paid)
            self.assertEqual(bill.signature, "")

        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_undo_ignores_forged_ids(self):
        self.client.force_login(self.owner)
        self.client.post(
            self.pay_url(self.bill_jan),
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(self.bill_feb.pk)]})
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("150.00"))

        # A foreign client's bill id must not be reverted.
        response = self.client.post(
            reverse("revert_client_bill", kwargs={
                "house_pk": self.house.pk,
                "client_pk": self.client_obj.pk,
                "pk": self.bill_jan.pk}),
            {"paid_together": [str(self.foreign_bill.pk)]},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.bill_jan.refresh_from_db()
        self.bill_feb.refresh_from_db()
        self.foreign_bill.refresh_from_db()
        self.assertFalse(self.bill_jan.is_paid)
        self.assertTrue(self.bill_feb.is_paid)   # not in paid_together: stays
        self.assertTrue(self.foreign_bill.is_paid)

        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("50.00"))

    def test_other_bill_multi_pay(self):
        other_jan = ClientOtherBill.objects.create(
            month="01", year="2026", comment="Repair fund",
            total_amount=Decimal("55.50"),
            house=self.house, client=self.client_obj, user=self.owner)
        other_feb = ClientOtherBill.objects.create(
            month="02", year="2026", comment="Repair fund Feb",
            total_amount=Decimal("22.25"),
            house=self.house, client=self.client_obj, user=self.owner)

        self.client.force_login(self.owner)
        url = reverse("edit_client_other_bill", kwargs={
            "house_pk": self.house.pk,
            "client_pk": self.client_obj.pk,
            "pk": other_jan.pk})

        response = self.client.post(
            url,
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(other_feb.pk)]},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Paid-Together"], str(other_feb.pk))

        other_jan.refresh_from_db()
        other_feb.refresh_from_db()
        self.assertTrue(other_jan.is_paid)
        self.assertTrue(other_feb.is_paid)
        self.assertEqual(other_jan.signature, self.SIGNATURE_B64)
        self.assertEqual(other_feb.signature, self.SIGNATURE_B64)

        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("77.75"))

    def test_no_js_multi_pay_redirects_and_pays_group(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.pay_url(self.bill_jan),
            {"is_paid": "on", "signature": "PHN2Zy8+",
             "pay_bill": [str(self.bill_feb.pk)]})

        self.assertEqual(response.status_code, 302)
        self.bill_jan.refresh_from_db()
        self.bill_feb.refresh_from_db()
        self.assertTrue(self.bill_jan.is_paid)
        self.assertTrue(self.bill_feb.is_paid)
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("150.00"))


class ClientBillSignatureValidationTests(TestCase):
    """The signature posted by the pad is validated server-side (#15):
    pure base64 that decodes to SVG markup, capped in size. Tampered
    payloads must not reach the DB and must not move the balance."""

    VALID_SVG_B64 = "PHN2Zy8+"  # <svg/>

    def setUp(self):
        self.owner = UserModel.objects.create_user(
            email="owner@test.bg", password="StrongPass123!")
        self.house = House.objects.create(
            town="Sofia", address="Test str. 1", entrance="A",
            money_balance=Decimal("0.00"), user=self.owner)
        self.client_obj = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=self.house, user=self.owner)
        self.bill = ClientMonthlyBill.objects.create(
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
            house=self.house, client=self.client_obj, user=self.owner)

    def pay(self, signature):
        self.client.force_login(self.owner)
        return self.client.post(
            reverse("edit_client_bill", kwargs={
                "house_pk": self.house.pk,
                "client_pk": self.client_obj.pk,
                "pk": self.bill.pk}),
            {"is_paid": "on", "signature": signature},
            HTTP_HX_REQUEST="true")

    def assert_bill_still_unpaid(self):
        self.bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.bill.is_paid)
        self.assertEqual(self.bill.signature, "")
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_valid_svg_signature_is_stored_and_paid(self):
        response = self.pay(self.VALID_SVG_B64)

        self.assertEqual(response.status_code, 200)
        self.bill.refresh_from_db()
        self.assertTrue(self.bill.is_paid)
        self.assertEqual(
            self.bill.signature, "data:image/svg+xml;base64,PHN2Zy8+")
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("100.00"))

    def test_invalid_base64_is_rejected(self):
        response = self.pay("!!!not-base64!!!")

        self.assert_bill_still_unpaid()
        self.assertContains(response, "Invalid signature payload.")

    def test_non_svg_payload_is_rejected(self):
        response = self.pay(base64.b64encode(b"hello world").decode())

        self.assert_bill_still_unpaid()

    def test_svg_without_svg_tag_is_rejected(self):
        response = self.pay(base64.b64encode(b"<rect/>").decode())

        self.assert_bill_still_unpaid()

    def test_oversized_payload_is_rejected(self):
        big = base64.b64encode(b"<svg>" + b"x" * (200 * 1024)).decode()

        self.pay(big)
        self.assert_bill_still_unpaid()

    def test_svg_with_xml_prolog_is_accepted(self):
        payload = base64.b64encode(
            b'<?xml version="1.0"?>'
            b'<svg xmlns="http://www.w3.org/2000/svg"></svg>').decode()

        response = self.pay(payload)

        self.assertEqual(response.status_code, 200)
        self.bill.refresh_from_db()
        self.assertTrue(self.bill.is_paid)

    def test_real_jsignature_payload_with_comment_is_accepted(self):
        # jSignature emits an XML prolog AND a comment before <svg> —
        # the exact payload the pad posts must pass (regression: the
        # first validator draft rejected it and blocked all payments).
        payload = base64.b64encode(
            b'<?xml version="1.0" encoding="utf-8" standalone="no"?>'
            b'<!--\nGenerated by jSignature 2.1\n-->'
            b'<svg xmlns="http://www.w3.org/2000/svg" version="1.1">'
            b'<path d="M10 10 L90 90" stroke="#000000" fill="none"/></svg>').decode()

        response = self.pay(payload)

        self.assertEqual(response.status_code, 200)
        self.bill.refresh_from_db()
        self.assertTrue(self.bill.is_paid)
        self.house.refresh_from_db()
        self.assertEqual(self.house.money_balance, Decimal("100.00"))

    def test_real_jsignature_payload_with_doctype_is_accepted(self):
        # The live pad emits a DOCTYPE after the prolog.
        payload = base64.b64encode(
            b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
            b'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
            b'"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
            b'<svg xmlns="http://www.w3.org/2000/svg" version="1.1"></svg>').decode()

        response = self.pay(payload)

        self.assertEqual(response.status_code, 200)
        self.bill.refresh_from_db()
        self.assertTrue(self.bill.is_paid)

    def test_doctype_with_internal_entity_subset_is_rejected(self):
        # An internal subset defines entities — the XXE vector. An
        # external-only DOCTYPE is allowed; this one is not.
        payload = base64.b64encode(
            b'<?xml version="1.0"?><!DOCTYPE svg ['
            b'<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            b'<svg>&xxe;</svg>').decode()

        response = self.pay(payload)

        self.assert_bill_still_unpaid()


class ClientBillSignatureOptionalTests(TestCase):
    """
    Per-house "Require signature on bills": with the option off, the
    payment UI renders no signature pad (HTMX modal and no-JS page
    alike) and a payment without any signature data still goes through;
    the reports show a Paid (Yes/No) column instead of Signature.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(
            email="owner@test.bg", password="StrongPass123!")

        cls.house = House.objects.create(
            town="Sofia", address="Test str. 1", entrance="A",
            money_balance=Decimal("0.00"), user=cls.owner,
            signature_required=False)

        cls.client_obj = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=cls.house, user=cls.owner)

        cls.monthly_bill = ClientMonthlyBill.objects.create(
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
            house=cls.house, client=cls.client_obj, user=cls.owner)

        cls.other_bill = ClientOtherBill.objects.create(
            month="01", year="2026", comment="Doorbell repair",
            total_amount=Decimal("40.00"),
            house=cls.house, client=cls.client_obj, user=cls.owner)

    def edit_url(self, bill, other=False):
        name = "edit_client_other_bill" if other else "edit_client_bill"
        return reverse(name, kwargs={
            "house_pk": self.house.pk,
            "client_pk": self.client_obj.pk,
            "pk": bill.pk,
        })

    # --- Payment UI without the pad -----------------------------------------

    def test_monthly_modal_omits_signature_pad(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            self.edit_url(self.monthly_bill), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-bill-modal")
        self.assertContains(response, 'id="id_is_paid"')
        self.assertNotContains(response, 'id="signature"')

    def test_other_bill_modal_omits_signature_pad(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            self.edit_url(self.other_bill, other=True), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-bill-modal")
        self.assertNotContains(response, 'id="signature"')

    def test_no_js_page_omits_signature_scripts(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.edit_url(self.monthly_bill))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "jSignature.js")
        self.assertNotContains(response, "signaturePad.js")
        # The payment flow itself is unchanged - its script still loads.
        self.assertContains(response, "billsPayments.js")

    def test_pay_monthly_bill_without_signature_credits_balance(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.edit_url(self.monthly_bill), {"is_paid": "on"},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.monthly_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.monthly_bill.is_paid)
        self.assertEqual(self.monthly_bill.signature, "")
        self.assertEqual(self.house.money_balance, Decimal("100.00"))

    def test_pay_other_bill_without_signature_credits_balance(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.edit_url(self.other_bill, other=True), {"is_paid": "on"},
            HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.other_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertTrue(self.other_bill.is_paid)
        self.assertEqual(self.other_bill.signature, "")
        self.assertEqual(self.house.money_balance, Decimal("40.00"))

    # --- Reports: Paid column instead of Signature ---------------------------

    def test_monthly_report_shows_paid_column_when_opted_out(self):
        self.client.force_login(self.owner)
        self.monthly_bill.is_paid = True
        self.monthly_bill.save(update_fields=["is_paid"])

        url = reverse("reports_bills", kwargs={"house_pk": self.house.pk})
        response = self.client.get(f"{url}?month=01&year=2026")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Signature")
        self.assertContains(response, 'data-label="Paid"')
        self.assertContains(response, ">Yes<")

    def test_monthly_report_shows_no_for_unpaid_bill_when_opted_out(self):
        self.client.force_login(self.owner)

        url = reverse("reports_bills", kwargs={"house_pk": self.house.pk})
        response = self.client.get(f"{url}?month=01&year=2026")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ">No<")

    def test_other_bills_report_shows_paid_column_when_opted_out(self):
        self.client.force_login(self.owner)
        self.other_bill.is_paid = True
        self.other_bill.save(update_fields=["is_paid"])

        url = reverse("reports_other_bills", kwargs={"house_pk": self.house.pk})
        response = self.client.get(
            f"{url}?month=01&year=2026&type_of_bill=Bill%20for%20all%20clients")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Signature")
        self.assertContains(response, 'data-label="Paid"')
        self.assertContains(response, ">Yes<")

    def test_other_bills_single_report_shows_paid_state_of_house_bill(self):
        self.client.force_login(self.owner)
        HouseOtherBill.objects.create(
            month="01", year="2026", comment="Facade repair",
            type_of_bill="Single bill", total_amount=Decimal("300.00"),
            house=self.house, user=self.owner)

        url = reverse("reports_other_bills", kwargs={"house_pk": self.house.pk})
        response = self.client.get(
            f"{url}?month=01&year=2026&type_of_bill=Single%20bill")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Signature")
        self.assertContains(response, ">No<")

    def test_report_keeps_signature_column_when_required(self):
        """The default workflow is untouched for houses with the option on."""
        self.client.force_login(self.owner)
        signature_house = House.objects.create(
            town="Varna", address="Sea str. 2", entrance="B",
            money_balance=Decimal("0.00"), user=self.owner,
            signature_required=True)
        signature_client = Client.objects.create(
            family_name="Petrov", floor=2, apartment="2",
            number_of_people=1, house=signature_house, user=self.owner)
        ClientMonthlyBill.objects.create(
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
            house=signature_house, client=signature_client, user=self.owner)

        url = reverse("reports_bills", kwargs={"house_pk": signature_house.pk})
        response = self.client.get(f"{url}?month=01&year=2026")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Signature")
        self.assertNotContains(response, 'data-label="Paid"')


class ClientBillsYearFilterTests(TestCase):
    """The Year chip group on the client bills lists: ?year= narrows to
    that year, composes with is_paid, and "" (the All chip) shows every
    year."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(
            email="owner@test.bg", password="StrongPass123!")
        cls.house = House.objects.create(
            town="Sofia", address="Test str. 1", entrance="A",
            money_balance=Decimal("0.00"), user=cls.owner)
        cls.client_obj = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=cls.house, user=cls.owner)

        bill_defaults = dict(
            electricity_lift=Decimal("0.00"), internet=Decimal("0.00"),
            maintenance_lift=Decimal("0.00"), fee_cleaner=Decimal("0.00"),
            fee_manager=Decimal("0.00"), fee_cashier=Decimal("0.00"),
            repairs=Decimal("0.00"), others=Decimal("0.00"),
            amount_old_debts=Decimal("0.00"),
            house=cls.house, client=cls.client_obj, user=cls.owner)

        cls.bill_2026 = ClientMonthlyBill.objects.create(
            month="01", year="2026", electricity_common=Decimal("100.00"),
            **bill_defaults)
        cls.bill_2025 = ClientMonthlyBill.objects.create(
            month="01", year="2025", electricity_common=Decimal("80.00"),
            **bill_defaults)

    def test_year_chip_filters_client_bills(self):
        self.client.force_login(self.owner)
        url = reverse("list_client_bills", kwargs={
            "house_pk": self.house.pk, "client_pk": self.client_obj.pk})

        response = self.client.get(f"{url}?year=2026&month=&is_paid=",
                                   HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.bill_2026.pk}"')
        self.assertNotContains(response, f'id="bill-row-{self.bill_2025.pk}"')

        response = self.client.get(f"{url}?year=&month=&is_paid=",
                                   HTTP_HX_REQUEST="true")

        self.assertContains(response, f'id="bill-row-{self.bill_2026.pk}"')
        self.assertContains(response, f'id="bill-row-{self.bill_2025.pk}"')
