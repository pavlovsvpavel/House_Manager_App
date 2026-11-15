from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
