from django.core import exceptions
from django.test import TestCase
from django.contrib.auth import get_user_model

from house_manager.houses.models import House

UserModel = get_user_model()


class HouseTests(TestCase):
    def setUp(self):
        user_data = {
            'email': 'admin@admin.bg',
            "password": "123456",
        }

        self.user = UserModel.objects.create_user(**user_data)

    def test_house_create__with_valid_data__expect_to_be_created(self):
        house_data = {
            "town": "Plovdiv",
            "address": "My address",
            "building_number": 777,
            "entrance": "A",
            "money_balance": 1000,
            "user": self.user,
        }

        house = House.objects.create(**house_data)

        self.assertIsNotNone(house)

    def test_house_create__when_town_contains_invalid_characters__expect_validation_error(self):
        house_data = {
            "town": "9Sofia9",
            "address": "My address",
            "building_number": 999,
            "entrance": "A",
            "money_balance": 1000,
            "user": self.user,
        }

        with self.assertRaises(exceptions.ValidationError) as ve:
            house = House.objects.create(**house_data)
            house.full_clean()

        exception = ve.exception
        town_exception = str(exception.error_dict["town"][0])

        self.assertEqual("['Field should contains only letters']", str(town_exception))
