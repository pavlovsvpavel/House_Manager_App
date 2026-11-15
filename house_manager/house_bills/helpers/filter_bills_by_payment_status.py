def filter_bills_by_payment_status(bills, is_paid, month):
    """Filter bills by payment state and/or month, independently.

    - ``?is_paid=False``  -> debts across all months
    - ``?month=01``       -> January, paid and unpaid
    - both together       -> narrowed further
    - ``None`` / ``""``   -> no-op ("" is the "All" months choice)
    """
    if is_paid == "True":
        bills = bills.filter(is_paid=True)
    elif is_paid == "False":
        bills = bills.filter(is_paid=False)

    if month:
        bills = bills.filter(month=month)

    return bills
