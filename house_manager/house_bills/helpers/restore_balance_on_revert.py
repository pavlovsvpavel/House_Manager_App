from django.db.models import F

from house_manager.houses.models import House


def restore_house_balance_on_revert(type_of_bill, house_id, bill_id):
    """Exact inverse of subtract_amount_from_house_balance: monthly bills
    were debited amount_without_repairs(), every other bill total_amount.
    Used by the revert (undo payment) endpoint."""
    house = House.objects.filter(id=house_id)
    bill = type_of_bill.objects.get(id=bill_id)

    if bill.__class__.__name__ == "HouseMonthlyBill":
        amount = bill.amount_without_repairs()
    else:
        amount = bill.total_amount

    house.update(money_balance=F('money_balance') + amount)
