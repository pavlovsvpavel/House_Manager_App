def filter_bills_by_payment_status(bills, is_paid, month, year=None):
    """Filter bills by payment state, month and/or year, independently.

    - ``?is_paid=False``  -> debts across all months
    - ``?month=01``       -> January, paid and unpaid
    - ``?year=2026``      -> only that year
    - any combination     -> narrowed further
    - ``None`` / ``""``   -> no-op ("" is the "All" chips choice)
    """
    if is_paid == "True":
        bills = bills.filter(is_paid=True)
    elif is_paid == "False":
        bills = bills.filter(is_paid=False)

    if month:
        bills = bills.filter(month=month)

    if year:
        bills = bills.filter(year=year)

    return bills
