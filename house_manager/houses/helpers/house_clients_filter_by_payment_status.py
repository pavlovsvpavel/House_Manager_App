from django.db.models import Q


def filter_by_payment_status(clients, is_paid):
    if is_paid is not None:
        if is_paid == 'True':
            clients = (
                clients
                .filter(
                    Q(client_monthly_bills__is_paid=True) |
                    Q(client_other_bills__is_paid=True)
                )
                .distinct()
            )

        elif is_paid == 'False':
            clients = (
                clients
                .filter(
                    Q(client_monthly_bills__is_paid=False) |
                    Q(client_other_bills__is_paid=False)
                )
                .distinct()
            )

        return clients

    return clients
