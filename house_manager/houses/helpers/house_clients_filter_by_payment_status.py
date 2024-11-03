from django.db.models import Q


def filter_by_payment_status(clients, is_paid, month):
    if month is not None and month != "":
        clients = clients.filter(
            Q(client_monthly_bills__month=month) |
            Q(client_other_bills__month=month)
        )

        if is_paid is not None:
            if is_paid == 'True':
                clients = clients.filter(
                    Q(client_monthly_bills__is_paid=True, client_monthly_bills__month=month) |
                    Q(client_other_bills__is_paid=True, client_monthly_bills__month=month)
                )
            elif is_paid == 'False':
                clients = clients.filter(
                    Q(client_monthly_bills__is_paid=False, client_monthly_bills__month=month) |
                    Q(client_other_bills__is_paid=False, client_monthly_bills__month=month)
                )

    return clients.distinct()
