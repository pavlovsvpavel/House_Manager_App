from house_manager.client_bills.models import ClientOtherBill
from house_manager.clients.models import Client
from house_manager.house_bills.models import HouseOtherBill
from house_manager.houses.models import House


def calculate_fees_other_bills(house_id, year, month, user_id):
    house_other_bills = (HouseOtherBill
                         .objects
                         .filter(house_id=house_id, year=year, month=month))

    house_clients = Client.objects.select_related('house').filter(house_id=house_id)
    total_apartments = House.objects.total_apartments(house_id=house_id)
    calculated_values = {}

    for client in house_clients:
        for obj in house_other_bills:
            for field in obj._meta.fields:
                field_value = getattr(obj, field.name)

                if field.name in ['id', 'client', 'house', 'user']:
                    continue

                if field.name in ['year', 'month', 'comment']:
                    calculated_values[field.name] = field_value
                    continue

                calculated_values[field.name] = field_value / total_apartments

            ClientOtherBill.objects.create(house_id=house_id,
                                           client_id=client.pk,
                                           user_id=user_id,
                                           **calculated_values)
