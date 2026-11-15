from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.houses.models import House
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill

UserModel = get_user_model()


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

        self.assertEqual(HouseMonthlyBill.objects.count(), 2)
        # Note: create views render a SweetAlert success page (HTTP 200 with
        # a JS redirect), not a 302.
