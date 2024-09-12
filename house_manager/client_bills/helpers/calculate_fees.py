from house_manager.client_bills.helpers.round_up_second_decimal import round_up_second_decimal
from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client
from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House


def calculate_fees(house_id, year, month, user_id):
    house_bills = (HouseMonthlyBill
                   .objects
                   .get(house_id=house_id, year=year, month=month))

    house_clients = Client.objects.select_related('house').filter(house_id=house_id)
    total_people = House.objects.total_people(house_id=house_id)
    total_people_using_lift = House.objects.total_people_using_lift(house_id=house_id)
    uninhabitable_apartments = House.objects.uninhabitable_apartments(house_id=house_id)
    total_apartments = House.objects.total_apartments(house_id=house_id) - uninhabitable_apartments
    calculated_values = {}

    for client in house_clients:
        for field in house_bills._meta.get_fields():
            field_value = getattr(house_bills, field.name)

            # Calculations based on apartment status - inhabitable (False)
            if not client.is_inhabitable:
                if field.name in ['id', 'total_amount', 'client', 'house', 'user']:
                    continue

                if field.name in ['year', 'month']:
                    calculated_values[field.name] = field_value
                    continue

                calculated_values[field.name] = 0

            # Calculations based on apartment status - occupation (True)
            elif client.is_occupied:
                if field.name in ['id', 'total_amount', 'client', 'house', 'user']:
                    continue

                if field.name in ['year', 'month']:
                    calculated_values[field.name] = field_value
                    continue

                # Calculation based on total people using lift or not using lift
                if field.name in ['maintenance_lift', 'electricity_lift'] and client.is_using_lift:
                    calculated_amount = (field_value / total_people_using_lift) * client.number_of_people
                    calculated_values[field.name] = round_up_second_decimal(calculated_amount)
                    continue

                elif field.name in ['maintenance_lift', 'electricity_lift'] and not client.is_using_lift:
                    calculated_values[field.name] = 0
                    continue

                # Calculation based on total apartments
                elif field.name in ['repairs', 'others', 'fee_manager_and_cashier']:
                    calculated_amount = field_value / total_apartments
                    calculated_values[field.name] = round_up_second_decimal(calculated_amount)
                    continue

                calculated_amount = (field_value / total_people) * client.number_of_people
                calculated_values[field.name] = round_up_second_decimal(calculated_amount)

            # Calculations based on apartment occupation (False)
            elif not client.is_occupied:
                if field.name in ['id', 'total_amount', 'client', 'house', 'user']:
                    continue

                if field.name in ['year', 'month']:
                    calculated_values[field.name] = field_value
                    continue

                if field.name in ['fee_manager_and_cashier', 'repairs', 'others']:
                    calculated_amount = field_value / total_apartments
                    calculated_values[field.name] = round_up_second_decimal(calculated_amount)
                    continue

                calculated_values[field.name] = 0

        ClientMonthlyBill.objects.create(house_id=house_id,
                                         client_id=client.pk,
                                         user_id=user_id,
                                         **calculated_values)
