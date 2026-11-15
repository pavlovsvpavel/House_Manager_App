from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.houses.models import House
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill

UserModel = get_user_model()


class HouseBillsSecurityTests(TestCase):
    """
    Regression tests for the Phase 0 security fixes:
    - house bill edit views must check object ownership on GET and POST (IDOR);
    - marking a bill paid must be idempotent (no balance changes on replay);
    - bill creation must verify that the session-selected house belongs to
      the logged-in user.
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

    def _prime_session_house(self, house_pk):
        session = self.client.session
        session["selected_house"] = house_pk
        session.save()

    # --- IDOR: edit house bills -------------------------------------------

    def test_edit_monthly_bill_get_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse("edit_house_bills", kwargs={"pk": self.monthly_bill.pk}))

        self.assertEqual(response.status_code, 403)
        self.monthly_bill.refresh_from_db()
        self.assertFalse(self.monthly_bill.is_paid)

    def test_edit_monthly_bill_post_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.post(
            reverse("edit_house_bills", kwargs={"pk": self.monthly_bill.pk}),
            {"is_paid": "on"},
        )

        self.assertEqual(response.status_code, 403)
        self.monthly_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.monthly_bill.is_paid)
        # Regression: the balance must not change via a foreign user's POST.
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_edit_other_bill_post_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.post(
            reverse("edit_other_house_bills", kwargs={"pk": self.other_bill.pk}),
            {"is_paid": "on"},
        )

        self.assertEqual(response.status_code, 403)
        self.other_bill.refresh_from_db()
        self.house.refresh_from_db()
        self.assertFalse(self.other_bill.is_paid)
        self.assertEqual(self.house.money_balance, Decimal("0.00"))

    def test_list_house_bills_blocked_for_other_user(self):
        self.client.force_login(self.attacker)
        self._prime_session_house(self.house.pk)

        response = self.client.get(reverse("list_house_bills", kwargs={"pk": self.house.pk}))

        # The session is primed, but the house does not belong to the user.
        self.assertEqual(response.status_code, 403)

    # --- Idempotency: replay must not re-debit the balance -----------------

    def test_mark_other_bill_paid_credits_balance_once(self):
        self.client.force_login(self.owner)
        self._prime_session_house(self.house.pk)

        url = reverse("edit_other_house_bills", kwargs={"pk": self.other_bill.pk})
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

    # --- Create: session-selected house must belong to the user ------------

    def test_create_house_bill_blocked_with_foreign_selected_house(self):
        self.client.force_login(self.attacker)
        self._prime_session_house(self.house.pk)

        response = self.client.post(reverse("create_house_bills"), {
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
