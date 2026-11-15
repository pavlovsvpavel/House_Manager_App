"""Shared summary-line numbers for the bills lists (client and house).

The payment modal's form action and the bill rows' revert URL carry the
list's query string (?is_paid / ?month), so the out-of-band summary swap
in a pay/undo response recomputes the same filtered view the user is
looking at (bugfix: the line used to go stale after an in-place
pay/undo).
"""
from decimal import Decimal

from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from house_manager.house_bills.helpers.filter_bills_by_payment_status import (
    filter_bills_by_payment_status,
)


def filtered_bills(bills, request):
    """Apply the bills list's GET filter (?is_paid / ?month) — no-op when
    neither parameter is present."""
    is_paid = request.GET.get("is_paid")
    month = request.GET.get("month")
    if is_paid is not None or month is not None:
        bills = filter_bills_by_payment_status(bills, is_paid, month)
    return bills


def bills_summary(bills):
    """Context for the summary line, computed over the (filtered) queryset."""
    unpaid = bills.filter(is_paid=False)
    return {
        "bills_count": bills.count(),
        "unpaid_count": unpaid.count(),
        "unpaid_total": unpaid.aggregate(
            total=Coalesce(Sum("total_amount"), Value(Decimal("0.00"))))["total"],
    }
