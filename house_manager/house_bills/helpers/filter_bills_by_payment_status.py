from django.db.models import Q


def filter_bills_by_payment_status(bills, is_paid):
    if is_paid == 'True':
        return bills.filter(Q(is_paid=True)).distinct()
    elif is_paid == 'False':
        return bills.filter(Q(is_paid=False)).distinct()

    return bills
