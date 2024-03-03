from django.db import models
from house_manager.common.mixins import MonthlyBill
from house_manager.houses.models import House


class HouseMonthlyBill(MonthlyBill):
    class Meta:
        unique_together = ["year", "month"]
        ordering = ["year", "month"]

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name='house_monthly_bills'
    )

    def __str__(self):
        return f"Added house bill for '{self.house}' for {self.month} {self.year}"
