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
    JANUARY = "01"
    FEBRUARY = "02"
    MARCH = "03"
    APRIL = "04"
    MAY = "05"
    JUNE = "06"
    JULY = "07"
    AUGUST = "08"
    SEPTEMBER = "09"
    OCTOBER = "10"
    NOVEMBER = "11"
    DECEMBER = "12"


class MonthlyBill(models.Model):
    MAX_MONTH_LENGTH = max(len(x) for _, x in MonthChoices.choices)
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
        verbose_name=_("Month"),
    )

    year = models.CharField(
        max_length=MAX_YEAR_LENGTH,
        blank=False,
        null=False,
        verbose_name=_("Year"),
    )

    electricity_common = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Electricity common"),
    )

    electricity_lift = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Electricity lift"),
    )

    internet = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Internet"),
    )

    maintenance_lift = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Lift maintenance"),
    )

    fee_cleaner = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Cleaner fee"),
    )

    fee_manager_and_cashier = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Manager/Cashier fee"),
    )

    repairs = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Repairs"),
    )

    others = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Other expenses"),
    )

    total_amount = models.GeneratedField(
        output_field=models.DecimalField(
            max_digits=MAX_DECIMAL_DIGITS,
            decimal_places=MAX_DECIMAL_PLACES,
        ),
        verbose_name=_("Total BGN"),
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

    is_paid = models.BooleanField(
        default=False,
        verbose_name=_("Paid"),
    )

    def get_month_name(self):
        return dict(MonthChoices.choices)[self.month]


class OtherBill(models.Model):
    MAX_MONTH_LENGTH = 10
    MAX_YEAR_LENGTH = 4
    MAX_DECIMAL_DIGITS = 10
    MAX_DECIMAL_PLACES = 2

    class Meta:
        abstract = True
        ordering = ["-year", "month"]

    month = models.CharField(
        max_length=MAX_MONTH_LENGTH,
        choices=MonthChoices.choices,
        blank=False,
        null=False,
        verbose_name=_("Month"),
    )

    year = models.CharField(
        max_length=MAX_YEAR_LENGTH,
        blank=False,
        null=False,
        verbose_name=_("Year"),
    )

    comment = models.TextField(
        blank=False,
        null=False,
        verbose_name=_("Comment"),
    )

    total_amount = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        verbose_name=_("Total BGN"),
    )

    is_paid = models.BooleanField(
        default=False,
        verbose_name=_("Paid"),
    )

    def get_month_name(self):
        return dict(MonthChoices.choices)[self.month]
