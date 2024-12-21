from django.db.models import Q


def filter_bills_by_payment_status(bills, is_paid, month):
    if month is not None and month != "":
        bills = bills.filter(
            Q(month=month) |
            Q(month=month)
        )
        if is_paid == 'True':
            return bills.filter(Q(is_paid=True, month=month)).distinct()
        elif is_paid == 'False':
            return bills.filter(Q(is_paid=False, month=month)).distinct()

    return bills
