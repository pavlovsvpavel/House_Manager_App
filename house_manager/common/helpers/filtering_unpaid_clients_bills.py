from decimal import Decimal
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce


# Calculate unpaid bills from previous months for each client
def filtering_unpaid_clients_bills(current_house, clients_bills, selected_year, selected_month):
    unpaid_bills = {}

    for client_bill in clients_bills:
        client = client_bill.client
        total_unpaid = (current_house.client_house_monthly_bills
        .filter(
            client=client,
            is_paid=False
        )
        .exclude(
            Q(year=selected_year, month__gte=selected_month) |
            Q(year__gt=selected_year)
        )

        .aggregate(total_unpaid=Coalesce(Sum("total_amount"),
                                         Value(Decimal("0.00"))))["total_unpaid"]
        )
        unpaid_bills[client.id] = total_unpaid

    return unpaid_bills

