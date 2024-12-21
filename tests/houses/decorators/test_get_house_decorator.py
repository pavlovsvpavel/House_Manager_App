from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase, RequestFactory
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from house_manager.houses.decorators import get_current_house_id
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
        request = self.factory.get(reverse('details_house', kwargs={'pk': house_id}))

        request.user = self.user

        @get_current_house_id
        def dummy_view(request, *args, **kwargs):
            return True

        result = dummy_view(request, pk=house_id)

        self.assertTrue(result)

    def test_invalid_house_id__expect_does_not_exist_error(self):
        invalid_house_id = 999

        request = self.factory.get(reverse('details_house', kwargs={'pk': invalid_house_id}))
        request.user = self.user

        @get_current_house_id
        def dummy_view(request, *args, **kwargs):
            return True

        with self.assertRaises(Http404):
            dummy_view(request, pk=invalid_house_id)

    def test_not_owner__expect_permission_denied_error(self):
        house_id = self.house.id
        user_data = {
            'email': 'other_user@admin.bg',
            "password": "654321",
        }

        other_user = UserModel.objects.create_user(**user_data)

        request = self.factory.get(reverse('details_house', kwargs={'pk': house_id}))
        request.user = other_user

        @get_current_house_id
        def dummy_view(request, *args, **kwargs):
            return True

        with self.assertRaises(PermissionDenied):
            dummy_view(request, pk=house_id)
