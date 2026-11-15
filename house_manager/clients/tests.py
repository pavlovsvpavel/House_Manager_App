from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.clients.models import Client
from house_manager.houses.models import House

UserModel = get_user_model()


class ClientOwnershipTests(TestCase):
    """
    Regression tests for client detail/edit/delete routes (mounted at
    /houses/<house_pk>/clients/<route>/<pk>/): the client in the URL must
    belong to the logged-in user and to the house in the URL.
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

    def test_client_detail_allowed_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            "details_client", kwargs={"house_pk": self.house.pk, "pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 200)

    def test_client_detail_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse(
            "details_client", kwargs={"house_pk": self.house.pk, "pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 404)

    def test_client_edit_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse(
            "edit_client", kwargs={"house_pk": self.house.pk, "pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 404)

    def test_client_delete_blocked_for_other_user(self):
        self.client.force_login(self.attacker)

        response = self.client.get(reverse(
            "delete_client", kwargs={"house_pk": self.house.pk, "pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 404)

    def test_client_blocked_when_house_pk_does_not_own_client(self):
        """Same owner, same house URL — but the client belongs to another
        house of that owner must 404 (parent/child URL mismatch)."""
        self.client.force_login(self.owner)
        other_house = House.objects.create(
            town="Plovdiv",
            address="Other str. 2",
            entrance="B",
            money_balance=Decimal("0.00"),
            user=self.owner,
        )

        response = self.client.get(reverse(
            "details_client", kwargs={"house_pk": other_house.pk, "pk": self.client_obj.pk}))

        self.assertEqual(response.status_code, 404)
