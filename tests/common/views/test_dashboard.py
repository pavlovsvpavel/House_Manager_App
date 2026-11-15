from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse

from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.common.views import DashboardView
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill
from house_manager.houses.helpers.house_clients_filter_by_payment_status import (
    house_clients_filter_by_payment_status,
)
from house_manager.houses.models import House
from house_manager.clients.models import Client

UserModel = get_user_model()


def monthly_bill_data(total):
    """Component values for a MonthlyBill whose generated total is `total`."""
    return {
        "month": "10",
        "year": "2026",
        "electricity_common": total,
        "electricity_lift": 0,
        "internet": 0,
        "maintenance_lift": 0,
        "fee_cleaner": 0,
        "fee_manager": 0,
        "fee_cashier": 0,
        "repairs": 0,
        "others": 0,
    }


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


class DashboardKpisTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserModel.objects.create_user(
            email='admin@admin.bg', password='123456')
        self.houses = House.objects.bulk_create([
            House(town="Sofia", address="Sofia's address",
                  building_number=999, entrance="A",
                  money_balance=1000, user=self.user),
            House(town="Plovdiv", address="Plovdiv's address",
                  building_number=111, entrance="B",
                  money_balance=500, user=self.user),
        ])
        self.house = self.houses[0]
        self.client = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=self.house, user=self.user)
        self.dashboard_url = reverse('dashboard')

    def get_house_context(self):
        request = self.factory.get(self.dashboard_url)
        request.user = self.user
        response = DashboardView.as_view()(request)
        return {h.pk: h for h in response.context_data['houses']}

    def test_kpis__client_due_covers_monthly_and_other_bills(self):
        ClientMonthlyBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            **monthly_bill_data(100))
        ClientMonthlyBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            **monthly_bill_data(50))
        ClientMonthlyBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            is_paid=True, **monthly_bill_data(70))
        ClientOtherBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            month="10", year="2026", comment="repair", total_amount=30)

        house = self.get_house_context()[self.house.pk]

        self.assertEqual(house.unpaid_bills_count, 3)
        self.assertEqual(house.unpaid_bills_total, 180)

    def test_kpis__house_bills_split_monthly_and_other(self):
        ClientMonthlyBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            **monthly_bill_data(100))
        HouseMonthlyBill.objects.create(
            house=self.house, user=self.user, **monthly_bill_data(200))
        HouseMonthlyBill.objects.create(
            house=self.house, user=self.user, is_paid=True,
            **{**monthly_bill_data(90), "month": "09"})
        HouseOtherBill.objects.create(
            house=self.house, user=self.user,
            month="10", year="2026", comment="facade",
            type_of_bill="Single bill", total_amount=40)

        house = self.get_house_context()[self.house.pk]

        self.assertEqual(house.unpaid_house_monthly_total, 200)
        self.assertEqual(house.unpaid_house_other_total, 40)

    def test_kpis__paid_bills_count_covers_monthly_and_other(self):
        ClientMonthlyBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            is_paid=True, **monthly_bill_data(70))
        ClientOtherBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            month="10", year="2026", comment="done", total_amount=20,
            is_paid=True)
        ClientMonthlyBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            **monthly_bill_data(100))

        house = self.get_house_context()[self.house.pk]

        self.assertEqual(house.paid_bills_count, 2)
        self.assertEqual(house.unpaid_bills_count, 1)

    def test_kpis__no_bills__expect_zeroed_kpis(self):
        house = self.get_house_context()[self.house.pk]

        self.assertEqual(house.unpaid_bills_count, 0)
        self.assertEqual(house.unpaid_bills_total, 0)
        self.assertEqual(house.unpaid_house_monthly_total, 0)
        self.assertEqual(house.unpaid_house_other_total, 0)

    def test_kpis__bills_of_other_house_do_not_leak(self):
        other_house = self.houses[1]
        ClientMonthlyBill.objects.create(
            house=other_house, user=self.user, **monthly_bill_data(300))
        HouseMonthlyBill.objects.create(
            house=other_house, user=self.user, **monthly_bill_data(400))

        house = self.get_house_context()[self.house.pk]

        self.assertEqual(house.unpaid_bills_count, 0)
        self.assertEqual(house.unpaid_bills_total, 0)
        self.assertEqual(house.unpaid_house_monthly_total, 0)
        self.assertEqual(house.unpaid_house_other_total, 0)

    def test_payment_status_filter__unpaid_without_month(self):
        paid_client = Client.objects.create(
            family_name="Petrova", floor=2, apartment="2",
            number_of_people=1, house=self.house, user=self.user)
        ClientMonthlyBill.objects.create(
            client=self.client, house=self.house, user=self.user,
            **monthly_bill_data(100))
        ClientOtherBill.objects.create(
            client=paid_client, house=self.house, user=self.user,
            month="10", year="2026", comment="paid", total_amount=20,
            is_paid=True)

        clients = house_clients_filter_by_payment_status(
            Client.objects.filter(house=self.house), 'False', None)

        self.assertEqual(list(clients), [self.client])
