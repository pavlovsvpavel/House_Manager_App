from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.models import Profile
from house_manager.common.mixins import TimeStampModel, MonthlyBill
from house_manager.common.validators import validate_char_field
from house_manager.houses.managers import SingleHouseManager

UserModel = get_user_model()


class House(TimeStampModel):
    MAX_TOWN_LENGTH = 20
    MAX_ADDRESS_LENGTH = 100
    MAX_ENTRANCE_LENGTH = 2
    MIN_VALUE = 0

    town = models.CharField(
        max_length=MAX_TOWN_LENGTH,
        validators=[
            validate_char_field,
        ],
        blank=False,
        null=False,
        verbose_name=_("Town"),
    )

    address = models.CharField(
        max_length=MAX_ADDRESS_LENGTH,
        blank=False,
        null=False,
        verbose_name=_("Address"),
    )

    building_number = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Building number"),
    )

    entrance = models.CharField(
        max_length=MAX_ENTRANCE_LENGTH,
        blank=False,
        null=False,
        verbose_name=_("Entrance"),
    )

    money_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Current balance"),
    )

    fixed_monthly_taxes = models.BooleanField(
        default=False,
        blank=False,
        verbose_name=_("Fixed monthly taxes")
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
    )

    objects = SingleHouseManager()

    def __str__(self):
        return (f"{self.town}, {self.address}, "
                f"{self.building_number}, {self.entrance}")


class HouseCalculationsOptions(TimeStampModel):
    class Meta:
        unique_together = ('house', 'user')
        verbose_name = _("House Calculation Option")
        verbose_name_plural = _("House Calculation Options")

    @classmethod
    def get_monthly_bill_field_choices(cls):
        excluded_fields = {'id', 'month', 'year', 'is_paid', 'signature', 'created_at', 'updated_at', 'total_amount'}
        choices = []

        for field in MonthlyBill._meta.get_fields():
            if field.name not in excluded_fields:
                label = getattr(field, 'verbose_name', field.name)
                choices.append((field.name, label))
        return choices

    based_on_apartment = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        verbose_name=_("Selected fields based on apartments")
    )

    based_on_total_people = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        verbose_name=_("Selected fields based on total people")
    )

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name="house_calculations_options"
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"Calculation options for house {self.house}"

    @property
    def field_choices(self):
        if not hasattr(self, '_cached_field_choices'):
            self._cached_field_choices = self.get_monthly_bill_field_choices()
        return self._cached_field_choices
