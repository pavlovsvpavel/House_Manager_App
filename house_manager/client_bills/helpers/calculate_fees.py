from house_manager.client_bills.helpers.handlers import handle_client, handle_not_used_fields, handle_text_fields, \
    handle_calculation_options
from house_manager.client_bills.helpers.round_up_second_decimal import round_up_second_decimal
from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client
from house_manager.common.helpers.filtering_unpaid_client_bills import filtering_unpaid_client_bills
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
    bills_based_on_apartments, bills_based_on_total_people = handle_calculation_options(house_id, user_id)

    for client in house_clients:
        calculated_values = {}
        inhabitable_apartment = handle_client(client)

        for field in house_bills._meta.get_fields():
            field_name = field.name
            field_value = getattr(house_bills, field_name)
            not_used_field = handle_not_used_fields(field_name)
            text_field = handle_text_fields(field_name)

            if not_used_field:
                continue

            if text_field:
                calculated_values[field_name] = field_value
                continue

            # Calculations based on apartment status - inhabitable (False)
            if not inhabitable_apartment:
                calculated_values[field_name] = 0
                continue

            # Calculations based on total people
            if field_name in bills_based_on_total_people:
                # Calculations based on apartment status - occupation (True)
                if client.is_occupied:
                    # Calculations based on using lift (True)
                    if field_name in ['maintenance_lift', 'electricity_lift']:
                        if client.is_using_lift:
                            calculated_amount = (field_value / total_people_using_lift) * client.number_of_people
                            calculated_values[field_name] = round_up_second_decimal(calculated_amount)
                        else:
                            calculated_values[field_name] = 0
                    # Calculations based on using lift (False)
                    else:
                        calculated_amount = (field_value / total_people) * client.number_of_people
                        calculated_values[field_name] = round_up_second_decimal(calculated_amount)

                # Calculations based on apartment status - occupation (False)
                elif not client.is_occupied:
                    calculated_values[field_name] = 0

            # Calculations based on apartments
            elif field_name in bills_based_on_apartments:
                calculated_amount = field_value / total_apartments
                calculated_values[field_name] = round_up_second_decimal(calculated_amount)

        # Calculate unpaid bills from previous months
        unpaid_bills = filtering_unpaid_client_bills(client, year, month)

        ClientMonthlyBill.objects.create(
            house_id=house_id,
            client_id=client.pk,
            user_id=user_id,
            amount_old_debts=unpaid_bills,
            **calculated_values
        )
