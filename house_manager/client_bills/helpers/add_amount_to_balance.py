from django.db.models import F

from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.houses.models import House


def add_amount_to_house_balance(type_of_bill, house_id, bill_id):
    house = House.objects.filter(id=house_id)
    bill = type_of_bill.objects.get(id=bill_id)

    amount = bill.total_amount

    house.update(money_balance=F('money_balance') + amount)
