from django.contrib.auth import get_user_model
from django.test import TestCase

from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.clients.models import Client
from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House

UserModel = get_user_model()

class TestClientBillCalculations(TestCase):
    def setUp(self):
        user_data = {
            "email": "admin@admin.bg",
            "password": "123456",
        }

        self.user = UserModel.objects.create_user(**user_data)

        house_data = {
            "town": "Sofia",
            "address": "Mladost",
            "building_number": 212,
            "entrance": "A",
            "money_balance": 0,
            "user": self.user,
        }

        self.house = House.objects.create(**house_data)

        test_client_data = {
            "family_name": "Ivanovi",
            "floor": 1,
            "apartment": 3,
            "number_of_people": 0,
            "house_id": self.house.id,
            "user_id": self.user.id,
        }

        self.test_client = Client.objects.create(**test_client_data)

        regular_client_data = {
            "family_name": "Georgievi",
            "floor": 3,
            "apartment": 6,
            "number_of_people": 3,
            "house_id": self.house.id,
            "user_id": self.user.id,
        }

        self.regular_client = Client.objects.create(**regular_client_data)

        monthly_bill_data = {
            "month": "01",
            "year": "2024",
            "electricity_common": 1,
            "electricity_lift": 1,
            "internet": 1,
            "maintenance_lift": 1,
            "fee_cleaner": 1,
            "fee_manager_and_cashier": 1,
            "repairs": 1,
            "others": 1,
            "user_id": self.user.id,
            "house_id": self.house.id,
        }

        self.monthly_bill = HouseMonthlyBill.objects.create(**monthly_bill_data)

    def test_client_bill__when__is_inhabitable__is_false(self):
        self.test_client.is_using_lift = True
        self.test_client.is_occupied = True
        self.test_client.is_inhabitable = False

        self.test_client.save()
        calculate_fees(self.house.id, self.monthly_bill.year, self.monthly_bill.month, self.user.id)

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year, month=self.monthly_bill.month).first()

        result = client_bill.total_amount
        expected = 0

        self.assertEqual(result, expected)

    def test_client_bill__when__is_inhabitable__is_true__and__is_using_lift__is_true(self):
        self.test_client.is_using_lift = True
        self.test_client.is_occupied = True
        self.test_client.is_inhabitable = True
        self.test_client.number_of_people = 1

        self.test_client.save()
        calculate_fees(self.house.id, self.monthly_bill.year, self.monthly_bill.month, self.user.id)

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year, month=self.monthly_bill.month).first()

        electricity_common_result = client_bill.electricity_common
        electricity_common_expected = 0.25
        self.assertEqual(electricity_common_result, electricity_common_expected)

        electricity_lift_result = client_bill.electricity_lift
        electricity_lift_expected = 0.25
        self.assertEqual(electricity_lift_result, electricity_lift_expected)

        internet_result = client_bill.internet
        internet_expected = 0.25
        self.assertEqual(internet_result, internet_expected)

        maintenance_lift_result = client_bill.maintenance_lift
        maintenance_lift_expected = 0.25
        self.assertEqual(maintenance_lift_result, maintenance_lift_expected)

        fee_cleaner_result = client_bill.fee_cleaner
        fee_cleaner_expected = 0.25
        self.assertEqual(fee_cleaner_result, fee_cleaner_expected)

        fee_manager_result = client_bill.fee_manager_and_cashier
        fee_manager_expected = 0.5
        self.assertEqual(fee_manager_result, fee_manager_expected)

        repairs_result = client_bill.repairs
        repairs_expected = 0.5
        self.assertEqual(repairs_result, repairs_expected)

        others_result = client_bill.others
        others_expected = 0.5
        self.assertEqual(others_result, others_expected)


        total_amount_result = client_bill.total_amount
        total_amount_expected = 2.75

        self.assertEqual(total_amount_result, total_amount_expected)

    def test_client_bill__when__is_occupied__is_false(self):
        self.test_client.is_using_lift = True
        self.test_client.is_occupied = False
        self.test_client.is_inhabitable = True

        self.test_client.save()
        calculate_fees(self.house.id, self.monthly_bill.year, self.monthly_bill.month, self.user.id)

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year, month=self.monthly_bill.month).first()

        fee_manager_and_cashier_result = client_bill.fee_manager_and_cashier
        fee_manager_and_cashier_expected = 0.5
        self.assertEqual(fee_manager_and_cashier_result, fee_manager_and_cashier_expected)

        repairs_result = client_bill.repairs
        repairs_expected = 0.5
        self.assertEqual(repairs_result, repairs_expected)

        others_result = client_bill.others
        others_expected = 0.5
        self.assertEqual(others_result, others_expected)

        total_amount_result = client_bill.total_amount
        total_amount_expected = 1.5
        self.assertEqual(total_amount_result, total_amount_expected)

    def test_client_bill__when__is_using_lift__is_false(self):
        self.test_client.is_using_lift = False
        self.test_client.is_occupied = True
        self.test_client.is_inhabitable = True
        self.test_client.number_of_people = 1

        self.test_client.save()
        calculate_fees(self.house.id, self.monthly_bill.year, self.monthly_bill.month, self.user.id)

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year, month=self.monthly_bill.month).first()

        electricity_common_result = client_bill.electricity_common
        electricity_common_expected = 0.25
        self.assertEqual(electricity_common_result, electricity_common_expected)

        electricity_lift_result = client_bill.electricity_lift
        electricity_lift_expected = 0
        self.assertEqual(electricity_lift_result, electricity_lift_expected)

        internet_result = client_bill.internet
        internet_expected = 0.25
        self.assertEqual(internet_result, internet_expected)

        maintenance_lift_result = client_bill.maintenance_lift
        maintenance_lift_expected = 0
        self.assertEqual(maintenance_lift_result, maintenance_lift_expected)

        fee_cleaner_result = client_bill.fee_cleaner
        fee_cleaner_expected = 0.25
        self.assertEqual(fee_cleaner_result, fee_cleaner_expected)

        fee_manager_result = client_bill.fee_manager_and_cashier
        fee_manager_expected = 0.5
        self.assertEqual(fee_manager_result, fee_manager_expected)

        repairs_result = client_bill.repairs
        repairs_expected = 0.5
        self.assertEqual(repairs_result, repairs_expected)

        others_result = client_bill.others
        others_expected = 0.5
        self.assertEqual(others_result, others_expected)

        total_amount_result = client_bill.total_amount
        total_amount_expected = 2.25

        self.assertEqual(total_amount_result, total_amount_expected)


