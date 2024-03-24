from django.contrib.auth import get_user_model
from django.db import models
from house_manager.common.mixins import MonthlyBill, OtherBill
from house_manager.houses.models import House

UserModel = get_user_model()


class HouseMonthlyBill(MonthlyBill):
    class Meta:
        unique_together = ("year", "month", "house")
        ordering = ("is_paid", "-year", "month")

    is_paid = models.BooleanField(
        default=False,
        verbose_name="Paid",
    )

    house = models.ForeignKey(
        to=House,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='house_monthly_bills'
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.RESTRICT,
    )

    def amount_without_repairs(self):
        return self.total_amount - self.repairs

    def __str__(self):
        return f"Bill for '{self.house}' for {self.month} {self.year}"


class HouseOtherBill(OtherBill):
    class Meta:
        unique_together = ["year", "month", "house"]
        ordering = ["-year", "month"]

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name='house_other_bills'
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.RESTRICT,
    )


