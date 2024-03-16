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
    total_apartments = House.objects.total_apartments(house_id=house_id)
    calculated_values = {}

    for client in house_clients:
        for field in house_bills._meta.get_fields():
            field_value = getattr(house_bills, field.name)

            if client.is_occupied:
                if field.name in ['id', 'total_amount', 'client', 'house', 'user']:
                    continue

                if field.name in ['year', 'month']:
                    calculated_values[field.name] = field_value
                    continue

                if field.name in ['maintenance_lift', 'electricity_lift'] and client.is_using_lift:
                    calculated_values[field.name] = (field_value / total_people_using_lift) * client.number_of_people
                    continue

                elif field.name in ['maintenance_lift', 'electricity_lift'] and not client.is_using_lift:
                    calculated_values[field.name] = 0
                    continue

                elif field.name in ['repairs', 'others']:
                    calculated_values[field.name] = field_value / total_apartments
                    continue

                calculated_values[field.name] = (field_value / total_people) * client.number_of_people

            elif not client.is_occupied:
                if field.name in ['id', 'total_amount', 'client', 'house', 'user']:
                    continue

                if field.name in ['year', 'month']:
                    calculated_values[field.name] = field_value
                    continue

                if field.name in ['repairs', 'others']:
                    calculated_values[field.name] = field_value / total_apartments
                    continue

                calculated_values[field.name] = 0

        ClientMonthlyBill.objects.create(house_id=house_id,
                                         client_id=client.pk,
                                         user_id=user_id,
                                         **calculated_values)
