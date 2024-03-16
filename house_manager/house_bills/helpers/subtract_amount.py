from django.db.models import F

from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House


def subtract_amount_from_house_balance(house_id, bill_id):
    house = House.objects.filter(id=house_id)
    bill = HouseMonthlyBill.objects.get(id=bill_id)

    amount = bill.amount_without_repairs()

    house.update(money_balance=F('money_balance') - amount)

