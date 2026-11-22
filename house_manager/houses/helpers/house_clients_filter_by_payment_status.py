from django.db.models import Q


def house_clients_filter_by_payment_status(clients, is_paid, month, year=None):
    """Narrow clients to those with bills matching the given facets.

    - ``?month=01``       -> clients with a bill in January (any year)
    - ``?year=2026``      -> clients with a bill in that year
    - ``?is_paid=False``  -> clients with unpaid bills
    - any combination     -> all facets must match the same bill
    - ``None`` / ``""``   -> no-op ("" is the "All" option of the select)
    """
    bill_filters = {}
    if month:
        bill_filters["month"] = month
    if year:
        bill_filters["year"] = year
    if is_paid in ("True", "False"):
        bill_filters["is_paid"] = is_paid == "True"

    if not bill_filters:
        return clients.distinct()

    matching_bill = Q()
    for related_name in ("client_monthly_bills", "client_other_bills"):
        bill_condition = Q()
        for field, value in bill_filters.items():
            bill_condition &= Q(**{f"{related_name}__{field}": value})
        matching_bill |= bill_condition

    return clients.filter(matching_bill).distinct()
