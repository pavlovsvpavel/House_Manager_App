from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client
from house_manager.houses.models import House
from house_manager.houses.views import HouseClientsDetailView

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


class HouseClientsListTest(TestCase):
    """The dashboard KPIs deep-link into this page with ?is_paid=...;
    the page itself renders a status label instead of filter controls."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserModel.objects.create_user(
            email='admin@admin.bg', password='123456')
        self.house = House.objects.create(
            town="Sofia", address="Sofia's address", building_number=999,
            entrance="A", money_balance=1000, user=self.user)
        self.client_unpaid = Client.objects.create(
            family_name="Ivanov", floor=1, apartment="1",
            number_of_people=2, house=self.house, user=self.user)
        self.client_paid = Client.objects.create(
            family_name="Petrov", floor=2, apartment="2",
            number_of_people=1, house=self.house, user=self.user)

        ClientMonthlyBill.objects.create(
            client=self.client_unpaid, house=self.house, user=self.user,
            **monthly_bill_data(100))
        ClientMonthlyBill.objects.create(
            client=self.client_paid, house=self.house, user=self.user,
            is_paid=True, **monthly_bill_data(70))

    def get(self, query=""):
        request = self.factory.get(f"/houses/{self.house.pk}/clients/{query}")
        request.user = self.user
        return HouseClientsDetailView.as_view()(request, house_pk=self.house.pk)

    def test__no_filter__expect_all_clients_and_all_status(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["bills_filter_status"], 'all')
        self.assertEqual(
            set(c.pk for c in response.context_data["clients"]),
            {self.client_unpaid.pk, self.client_paid.pk})

    def test__is_paid_false__expect_only_clients_with_unpaid_bills(self):
        response = self.get("?is_paid=False")

        self.assertEqual(response.context_data["bills_filter_status"], 'unpaid')
        self.assertEqual(
            [c.pk for c in response.context_data["clients"]],
            [self.client_unpaid.pk])

    def test__is_paid_true__expect_only_clients_with_paid_bills(self):
        response = self.get("?is_paid=True")

        self.assertEqual(response.context_data["bills_filter_status"], 'paid')
        self.assertEqual(
            [c.pk for c in response.context_data["clients"]],
            [self.client_paid.pk])
