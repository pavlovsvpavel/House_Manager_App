from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client
from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House


def perform_calculations(house_id, year, month):
    house_bills = (HouseMonthlyBill
                   .objects
                   .get(house_id=house_id, year=year, month=month))

    house_clients = Client.objects.select_related('house').filter(house_id=house_id)
    total_people = House.objects.total_people(house_id=house_id)
    total_people_using_lift = House.objects.total_people_using_lift(house_id=house_id)
    calculated_values = {}

    for client in house_clients:
        for field in house_bills._meta.get_fields():
            if field.name in ['id', 'total_amount', 'client', 'house']:
                continue

            field_value = getattr(house_bills, field.name)

            if field.name in ['year', 'month']:
                calculated_values[field.name] = field_value
                continue

            if field.name in ['maintenance_lift', 'electricity_lift'] and client.is_using_lift:
                calculated_values[field.name] = (field_value / total_people_using_lift) * client.number_of_people
                continue

            elif field.name in ['maintenance_lift', 'electricity_lift'] and not client.is_using_lift:
                calculated_values[field.name] = 0
                continue

            calculated_values[field.name] = (field_value / total_people) * client.number_of_people

        client_monthly_bill, created = (ClientMonthlyBill.
                                        objects.
                                        get_or_create(house_id=house_id,
                                                      client_id=client.pk,
                                                      defaults=calculated_values))
        if not created:
            for field_name, value in calculated_values.items():
                setattr(client_monthly_bill, field_name, value)
            client_monthly_bill.save()