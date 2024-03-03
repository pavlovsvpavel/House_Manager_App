from django.db import models

from house_manager.clients.models import Client
from house_manager.common.mixins import MonthlyBill
from house_manager.houses.models import House


class ClientMonthlyBill(MonthlyBill):
    client = models.ForeignKey(
        to=Client,
        on_delete=models.CASCADE,
        related_name='client_monthly_bills',
    )

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name='client_house_monthly_bills'
    )
