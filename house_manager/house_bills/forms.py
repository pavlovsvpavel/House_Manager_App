from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill


class HouseBaseBillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            verbose_name = ""

            try:
                model_field = self.Meta.model._meta.get_field(field_name)
                verbose_name = model_field.verbose_name
            except FieldDoesNotExist:
                verbose_name = field.label or field_name

            if field_name in ["month", "year", "type_of_bill"]:
                field.widget.choices = [('', verbose_name)] + list(field.widget.choices)[1:]

            field.widget.attrs['placeholder'] = verbose_name
            field.label = False


class HouseMonthlyBillForm(HouseBaseBillForm):
    class Meta:
        model = HouseMonthlyBill
        fields = ("month", "year", "electricity_common",
                  "electricity_lift", "internet", "maintenance_lift",
                  "fee_cleaner", "fee_manager", "fee_cashier", "repairs",
                  "others")


class HouseMonthlyBillEditForm(HouseBaseBillForm):
    """Amount correction for fixed-taxes houses: the nine expense fields
    stay editable while the bill is unpaid (``total_amount`` is a
    DB-generated column, so it follows automatically). Non-fixed houses
    never get this form — ``calculate_fees`` has already distributed
    their amounts to the client bills at creation, and editing them here
    would desync the two."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The base form identifies fields with placeholders (create-form
        # style). In the correction dialog every field is prefilled, so a
        # placeholder would never be seen — the template renders a real
        # label above each input instead, and a duplicate placeholder
        # would only add noise.
        for field in self.fields.values():
            field.widget.attrs.pop("placeholder", None)

    class Meta:
        model = HouseMonthlyBill
        fields = ("electricity_common", "electricity_lift", "internet",
                  "maintenance_lift", "fee_cleaner", "fee_manager",
                  "fee_cashier", "repairs", "others", "is_paid")


class HouseOtherBillForm(HouseBaseBillForm):
    class Meta:
        model = HouseOtherBill
        fields = ("month", "year", "comment", "type_of_bill", "total_amount")


class HouseFixedBillForm(HouseBaseBillForm):
    fixed_amount = forms.DecimalField(
        label=_("Amount"),
        max_digits=10,
        decimal_places=2,
        required=True
    )

    class Meta:
        model = HouseMonthlyBill
        fields = ("month", "year")