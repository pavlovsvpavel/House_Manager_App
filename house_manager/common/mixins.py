from django.db import models
from django.db.models import F
from django.utils.translation import gettext_lazy as _


class TimeStampModel(models.Model):
    class Meta:
        abstract = True

    created_on = models.DateTimeField(
        auto_now_add=True,
    )

    updated_on = models.DateTimeField(
        auto_now=True,
    )


class MonthChoices(models.TextChoices):
    JANUARY = "1", "January"
    FEBRUARY = "2", "February"
    MARCH = "3"
    APRIL = "4"
    MAY = "5"
    JUNE = "6"
    JULY = "7"
    AUGUST = "8"
    SEPTEMBER = "9"
    OCTOBER = "10"
    NOVEMBER = "11"
    DECEMBER = "12"


class MonthlyBill(models.Model):
    MAX_MONTH_LENGTH = 10
    MAX_YEAR_LENGTH = 4
    MAX_DECIMAL_DIGITS = 10
    MAX_DECIMAL_PLACES = 2

    class Meta:
        abstract = True

    month = models.CharField(
        max_length=MAX_MONTH_LENGTH,
        choices=MonthChoices.choices,
        blank=False,
        null=False,
    )

    year = models.CharField(
        max_length=MAX_YEAR_LENGTH,
        blank=False,
        null=False,
    )

    electricity_common = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    electricity_lift = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    internet = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    maintenance_lift = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    fee_cleaner = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    fee_manager_and_cashier = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    repairs = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    others = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
    )

    total_amount = models.GeneratedField(
        output_field=models.DecimalField(
            max_digits=MAX_DECIMAL_DIGITS,
            decimal_places=MAX_DECIMAL_PLACES,
        ),
        db_persist=True,
        expression=(
                F('electricity_common') +
                F('electricity_lift') +
                F('internet') +
                F('maintenance_lift') +
                F('fee_cleaner') +
                F('fee_manager_and_cashier') +
                F('repairs') +
                F('others')
        )
    )

    def get_month_name(self):
        return dict(MonthChoices.choices)[self.month]
