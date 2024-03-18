from django.contrib.auth import get_user_model
from django.db import models

from house_manager.clients.models import Client
from house_manager.common.mixins import MonthlyBill, OtherBill
from house_manager.houses.models import House

UserModel = get_user_model()


class ClientMonthlyBill(MonthlyBill):
    class Meta:
        ordering = ("-year", "month")

    is_paid = models.BooleanField(
        default=False,
        verbose_name="Paid",
    )

    client = models.ForeignKey(
        to=Client,
        on_delete=models.DO_NOTHING,
        related_name='client_monthly_bills',
    )

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name='client_house_monthly_bills'
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.RESTRICT,
    )


class ClientOtherBill(OtherBill):
    client = models.ForeignKey(
        to=Client,
        on_delete=models.DO_NOTHING,
        related_name='client_other_bills',
    )

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name='client_house_other_bills'
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.RESTRICT,
    )
