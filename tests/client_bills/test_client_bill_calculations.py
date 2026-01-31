from django.contrib.auth import get_user_model
from django.test import TestCase

from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.client_bills.helpers.calculate_fixed_bills import calculate_fixed_client_bills
from house_manager.clients.models import Client
from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House, HouseCalculationsOptions

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
            "fixed_monthly_taxes": False,
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
            "fee_manager": 1,
            "fee_cashier": 1,
            "repairs": 1,
            "others": 1,
            "user_id": self.user.id,
            "house_id": self.house.id,
        }

        self.monthly_bill = HouseMonthlyBill.objects.create(**monthly_bill_data)

        self.calculation_options, created = HouseCalculationsOptions.objects.update_or_create(
            house_id=self.house.id,
            user_id=self.user.id,
            defaults={
                "based_on_apartment": ['fee_manager', 'fee_cashier', 'repairs', 'others', 'internet'],
                "based_on_total_people": ['electricity_common', 'electricity_lift', 'maintenance_lift', 'fee_cleaner'],
            }
        )

    def test_calculate_fixed_client_bills__creates_correct_amounts_for_all_occupancy_types(self):
        """
        Test calculate_fixed_client_bills logic:
        1. Occupied + Lift = Full Amount
        2. Occupied + No Lift = Half Amount
        3. Unoccupied = 0 Amount
        """
        # 1. Setup Data
        self.house.fixed_monthly_taxes = True
        self.house.save()

        # Case A: Occupied + Lift (Should pay Full Amount)
        self.regular_client.is_occupied = True
        self.regular_client.is_using_lift = True
        self.regular_client.save()

        # Case B: Occupied + No Lift (Should pay 50%)
        self.test_client.is_occupied = True
        self.test_client.is_using_lift = False
        self.test_client.save()

        # Case C: Unoccupied (Should pay 0)
        # Create a new client specifically for this test case
        unoccupied_client = Client.objects.create(
            family_name="Empty Apartment",
            floor=1,
            apartment=10,
            number_of_people=0,
            house_id=self.house.id,
            user_id=self.user.id,
            is_occupied=False,
            is_using_lift=True
        )

        fixed_amount = 20.00

        # 2. Call the function
        calculate_fixed_client_bills(
            self.house.id,
            self.monthly_bill.year,
            self.monthly_bill.month,
            fixed_amount,
            self.user.id
        )

        # 3. Assertions for Case A (Lift User)
        regular_bill = self.regular_client.client_monthly_bills.filter(
            year=self.monthly_bill.year,
            month=self.monthly_bill.month
        ).first()
        self.assertIsNotNone(regular_bill)
        self.assertEqual(regular_bill.others, 20.00)
        self.assertEqual(regular_bill.total_amount, 20.00)

        # 4. Assertions for Case B (No Lift)
        test_bill = self.test_client.client_monthly_bills.filter(
            year=self.monthly_bill.year,
            month=self.monthly_bill.month
        ).first()
        self.assertIsNotNone(test_bill)
        self.assertEqual(test_bill.others, 10.00)
        self.assertEqual(test_bill.total_amount, 10.00)

        # 5. Assertions for Case C (Unoccupied)
        unoccupied_bill = unoccupied_client.client_monthly_bills.filter(
            year=self.monthly_bill.year,
            month=self.monthly_bill.month
        ).first()

        self.assertIsNotNone(unoccupied_bill, "Bill should be created even if apartment is empty")
        self.assertEqual(unoccupied_bill.others, 0.00, "Unoccupied apartment fee should be 0")
        self.assertEqual(unoccupied_bill.total_amount, 0.00, "Total amount for unoccupied should be 0")

    def test_client_bill__when__is_inhabitable__is_false(self):
        self.test_client.is_using_lift = True
        self.test_client.is_occupied = True
        self.test_client.is_inhabitable = False

        self.test_client.save()
        calculate_fees(self.house.id, self.monthly_bill.year, self.monthly_bill.month, self.user.id)

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year,
                                                                   month=self.monthly_bill.month).first()

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

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year,
                                                                   month=self.monthly_bill.month).first()

        electricity_common_result = client_bill.electricity_common
        electricity_common_expected = 0.25
        self.assertEqual(electricity_common_result, electricity_common_expected)

        electricity_lift_result = client_bill.electricity_lift
        electricity_lift_expected = 0.25
        self.assertEqual(electricity_lift_result, electricity_lift_expected)

        internet_result = client_bill.internet
        internet_expected = 0.5
        self.assertEqual(internet_result, internet_expected)

        maintenance_lift_result = client_bill.maintenance_lift
        maintenance_lift_expected = 0.25
        self.assertEqual(maintenance_lift_result, maintenance_lift_expected)

        fee_cleaner_result = client_bill.fee_cleaner
        fee_cleaner_expected = 0.25
        self.assertEqual(fee_cleaner_result, fee_cleaner_expected)

        fee_manager_result = client_bill.fee_manager
        fee_manager_expected = 0.5
        self.assertEqual(fee_manager_result, fee_manager_expected)

        fee_cashier_result = client_bill.fee_cashier
        fee_cashier_expected = 0.5
        self.assertEqual(fee_cashier_result, fee_cashier_expected)

        repairs_result = client_bill.repairs
        repairs_expected = 0.5
        self.assertEqual(repairs_result, repairs_expected)

        others_result = client_bill.others
        others_expected = 0.5
        self.assertEqual(others_result, others_expected)

        total_amount_result = client_bill.total_amount
        total_amount_expected = 3.50

        self.assertEqual(total_amount_result, total_amount_expected)

    def test_client_bill__when__is_occupied__is_false(self):
        self.test_client.is_using_lift = True
        self.test_client.is_occupied = False
        self.test_client.is_inhabitable = True

        self.test_client.save()
        calculate_fees(self.house.id, self.monthly_bill.year, self.monthly_bill.month, self.user.id)

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year,
                                                                   month=self.monthly_bill.month).first()

        internet_result = client_bill.internet
        internet_expected = 0.5
        self.assertEqual(internet_result, internet_expected)

        fee_manager_result = client_bill.fee_manager
        fee_manager_expected = 0.5
        self.assertEqual(fee_manager_result, fee_manager_expected)

        fee_cashier_result = client_bill.fee_cashier
        fee_cashier_expected = 0.5
        self.assertEqual(fee_cashier_result, fee_cashier_expected)

        repairs_result = client_bill.repairs
        repairs_expected = 0.5
        self.assertEqual(repairs_result, repairs_expected)

        others_result = client_bill.others
        others_expected = 0.5
        self.assertEqual(others_result, others_expected)

        total_amount_result = client_bill.total_amount
        total_amount_expected = 2.5
        self.assertEqual(total_amount_result, total_amount_expected)

    def test_client_bill__when__is_using_lift__is_false(self):
        self.test_client.is_using_lift = False
        self.test_client.is_occupied = True
        self.test_client.is_inhabitable = True
        self.test_client.number_of_people = 1

        self.test_client.save()
        calculate_fees(self.house.id, self.monthly_bill.year, self.monthly_bill.month, self.user.id)

        client_bill = self.test_client.client_monthly_bills.filter(year=self.monthly_bill.year,
                                                                   month=self.monthly_bill.month).first()

        electricity_common_result = client_bill.electricity_common
        electricity_common_expected = 0.25
        self.assertEqual(electricity_common_result, electricity_common_expected)

        electricity_lift_result = client_bill.electricity_lift
        electricity_lift_expected = 0
        self.assertEqual(electricity_lift_result, electricity_lift_expected)

        internet_result = client_bill.internet
        internet_expected = 0.5
        self.assertEqual(internet_result, internet_expected)

        maintenance_lift_result = client_bill.maintenance_lift
        maintenance_lift_expected = 0
        self.assertEqual(maintenance_lift_result, maintenance_lift_expected)

        fee_cleaner_result = client_bill.fee_cleaner
        fee_cleaner_expected = 0.25
        self.assertEqual(fee_cleaner_result, fee_cleaner_expected)

        fee_manager_result = client_bill.fee_manager
        fee_manager_expected = 0.5
        self.assertEqual(fee_manager_result, fee_manager_expected)

        fee_cashier_result = client_bill.fee_cashier
        fee_cashier_expected = 0.5
        self.assertEqual(fee_cashier_result, fee_cashier_expected)

        repairs_result = client_bill.repairs
        repairs_expected = 0.5
        self.assertEqual(repairs_result, repairs_expected)

        others_result = client_bill.others
        others_expected = 0.5
        self.assertEqual(others_result, others_expected)

        total_amount_result = client_bill.total_amount
        total_amount_expected = 3.00

        self.assertEqual(total_amount_result, total_amount_expected)
