from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
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
        related_name="house_monthly_bills"
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.RESTRICT,
    )

    def amount_without_repairs(self):
        return self.total_amount - self.repairs

    def __str__(self):
        return f"Bill for '{self.house}' for {self.month} {self.year}"


class TypeOfBillChoices(models.TextChoices):
    SINGLE_BILL = ("Single bill", _("Single bill"))
    BILL_FOR_ALL_CLIENTS = ("Bill for all clients", _("Bill for all clients"))


class HouseOtherBill(OtherBill):
    MAX_TYPE_OF_BILL_LENGTH = max(len(x) for _, x in TypeOfBillChoices.choices)

    class Meta:
        ordering = ("is_paid", "-year", "month")

    type_of_bill = models.CharField(
        max_length=MAX_TYPE_OF_BILL_LENGTH,
        choices=TypeOfBillChoices.choices,
        blank=False,
        null=False,
        verbose_name=_("Type of bill"),
    )

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name="house_other_bills"
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.RESTRICT,
    )

    def get_type_of_bill(self):
        return dict(TypeOfBillChoices.choices)[self.type_of_bill]

    def validate_unique(self, exclude=None):
        if self.type_of_bill == "Bill for all clients":
            existing_qs = type(self).objects.filter(
                year=self.year,
                month=self.month,
                house=self.house,
                type_of_bill="Bill for all clients"
            )
            if existing_qs:
                raise ValidationError(
                    _("Bill for all clients with those month and year already exists.")
                )

