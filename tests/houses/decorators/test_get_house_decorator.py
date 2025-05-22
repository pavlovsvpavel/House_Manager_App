from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse
from house_manager.houses.models import House

UserModel = get_user_model()


class GetHouseDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        user_data = {
            'email': 'admin@admin.bg',
            "password": "123456",
        }

        self.user = UserModel.objects.create_user(**user_data)

        house_data = {
            "town": "Sofia",
            "address": "Sofia's address",
            "building_number": 999,
            "entrance": "A",
            "money_balance": 1000,
            "user": self.user,
        }

        self.house = House.objects.create(**house_data)

    def test_valid_house_id(self):
        house_id = self.house.id
        self.client.force_login(self.user)
        response = self.client.get(reverse('details_house', kwargs={'pk': house_id}))

        self.assertEqual(response.status_code, 200)

    def test_invalid_house_id__expect_does_not_exist_error(self):
        invalid_house_id = 999
        self.client.force_login(self.user)
        response = self.client.get(reverse('details_house', kwargs={'pk': invalid_house_id}))

        self.assertEqual(response.status_code, 404)

    def test_not_owner__expect_permission_denied_error(self):
        house_id = self.house.id
        user_data = {
            'email': 'other_user@admin.bg',
            "password": "654321",
        }

        other_user = UserModel.objects.create_user(**user_data)
        self.client.force_login(other_user)
        response = self.client.get(reverse('details_house', kwargs={'pk': house_id}))

        self.assertEqual(response.status_code, 403)
