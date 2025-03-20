from decimal import Decimal
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce

from house_manager.client_bills.models import ClientMonthlyBill


# Calculate unpaid bills from previous months
def filtering_unpaid_client_bills(client, selected_year, selected_month):
    unpaid_bills = (
        ClientMonthlyBill.objects.filter(
            client=client,
            is_paid=False
        )
        .exclude(
            Q(year=selected_year, month__gte=selected_month) |
            Q(year__gt=selected_year)
        )
        .aggregate(amount_old_debts=Coalesce(Sum("total_amount"), Value(Decimal("0.00"))))["amount_old_debts"]
    )

    return unpaid_bills


