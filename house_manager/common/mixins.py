import datetime

from django.core.validators import MinValueValidator
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
    JANUARY = ("01", _("January"))
    FEBRUARY = ("02", _("February"))
    MARCH = ("03", _("March"))
    APRIL = ("04", _("April"))
    MAY = ("05", _("May"))
    JUNE = ("06", _("June"))
    JULY = ("07", _("July"))
    AUGUST = ("08", _("August"))
    SEPTEMBER = ("09", _("September"))
    OCTOBER = ("10", _("October"))
    NOVEMBER = ("11", _("November"))
    DECEMBER = ("12", _("December"))


class YearChoices(models.TextChoices):
    @classmethod
    def previous_and_next_years(cls):
        current_year = datetime.date.today().year
        period = 2
        years = [(str(year), str(year)) for year in range(current_year - 1, current_year + period)]

        return years


class MonthlyBill(models.Model):
    MAX_MONTH_LENGTH = max(len(x) for _, x in MonthChoices.choices)
    MAX_YEAR_LENGTH = max(len(x) for _, x in YearChoices.previous_and_next_years())
    MAX_DECIMAL_DIGITS = 10
    MAX_DECIMAL_PLACES = 2
    MIN_VALUE = 0

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
        choices=YearChoices.previous_and_next_years(),
        blank=False,
        null=False,
        verbose_name=_("Year"),
    )

    electricity_common = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Electricity common"),
    )

    electricity_lift = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Electricity lift"),
    )

    internet = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Internet"),
    )

    maintenance_lift = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Lift maintenance"),
    )

    fee_cleaner = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Cleaner fee"),
    )

    fee_manager = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Manager fee"),
    )

    fee_cashier = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Cashier fee"),
    )

    repairs = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Repairs fund"),
    )

    others = models.DecimalField(
        max_digits=MAX_DECIMAL_DIGITS,
        decimal_places=MAX_DECIMAL_PLACES,
        blank=False,
        null=False,
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Other expenses"),
    )

    total_amount = models.GeneratedField(
        output_field=models.DecimalField(
            max_digits=MAX_DECIMAL_DIGITS,
            decimal_places=MAX_DECIMAL_PLACES,
        ),
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
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

    signature = models.TextField(
        default="",
    )

    def get_month_name(self):
        return dict(MonthChoices.choices)[self.month]


class OtherBill(models.Model):
    MAX_MONTH_LENGTH = max(len(x) for _, x in MonthChoices.choices)
    MAX_YEAR_LENGTH = max(len(x) for _, x in YearChoices.previous_and_next_years())
    MAX_DECIMAL_DIGITS = 10
    MAX_DECIMAL_PLACES = 2
    MIN_VALUE = 0

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
        choices=YearChoices.previous_and_next_years(),
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
        validators=(
            MinValueValidator(MIN_VALUE, message=_("Please enter a value greater than zero")),
        ),
        verbose_name=_("Total BGN"),
    )

    is_paid = models.BooleanField(
        default=False,
        verbose_name=_("Paid"),
    )

    signature = models.TextField(
        default="",
        blank=False,
        null=False,
    )

    def get_month_name(self):
        return dict(MonthChoices.choices)[self.month]
