from house_manager.clients.models import Client
from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.common.helpers.filtering_unpaid_client_bills import filtering_unpaid_client_bills


def calculate_fixed_client_bills(house_id, year, month, fixed_amount, user_id):
    clients = Client.objects.filter(house_id=house_id)

    client_bills_to_create = []

    for client in clients:
        if client.is_occupied:
            if client.is_using_lift:
                amount_to_pay = fixed_amount
            else:
                amount_to_pay = fixed_amount / 2
        else:
            amount_to_pay = 0

        unpaid_bills = filtering_unpaid_client_bills(client, year, month)

        bill = ClientMonthlyBill(
            client=client,
            year=year,
            month=month,
            house_id=house_id,
            user_id=user_id,

            electricity_common=0,
            electricity_lift=0,
            internet=0,
            maintenance_lift=0,
            fee_cleaner=0,
            fee_manager=0,
            fee_cashier=0,
            repairs=0,
            others=amount_to_pay,
            amount_old_debts=unpaid_bills
        )
        client_bills_to_create.append(bill)

    ClientMonthlyBill.objects.bulk_create(client_bills_to_create)

    return len(client_bills_to_create)
