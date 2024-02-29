from django.db import models

from house_manager.clients.models import Client
from house_manager.common.mixins import MonthlyBill


class ClientMonthlyBill(MonthlyBill):
    client = models.ForeignKey(
        to=Client,
        on_delete=models.CASCADE,
        related_name='client_monthly_bills',
    )
