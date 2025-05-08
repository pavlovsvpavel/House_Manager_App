from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse

from house_manager.common.views import DashboardView
from house_manager.houses.models import House

UserModel = get_user_model()


class DashboardTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        user_data = {
            'email': 'admin@admin.bg',
            "password": "123456",
        }

        self.user = UserModel.objects.create_user(**user_data)
        self.dashboard_url = reverse('dashboard')

        houses_data = [
            House(town="Sofia",
                  address="Sofia's address",
                  building_number=999,
                  entrance="A",
                  money_balance=1000,
                  user=self.user
                  ),
            House(town="Plovdiv",
                  address="Plovdiv's address",
                  building_number=111,
                  entrance="B",
                  money_balance=500,
                  user=self.user
                  )
        ]
        self.houses = House.objects.bulk_create(houses_data)

    def test_dashboard_view__logged_in_user__expect_house_list_with_two_houses(self):
        request = self.factory.get(self.dashboard_url)
        request.user = self.user
        response = DashboardView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('houses', response.context_data)
        self.assertEqual(len(response.context_data['houses']), 2)

    def test_dashboard_view__other_logged_in_user__expect_house_list_with_zero_houses(self):
        request = self.factory.get(self.dashboard_url)
        user_data = {
            'email': 'another_user@admin.bg',
            "password": "654321",
        }

        self.other_user = UserModel.objects.create_user(**user_data)
        request.user = self.other_user
        response = DashboardView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('houses', response.context_data)
        self.assertEqual(len(response.context_data['houses']), 0)
