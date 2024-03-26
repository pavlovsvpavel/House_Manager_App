from django import forms
from django.utils.translation import gettext_lazy as _
from house_manager.house_bills.helpers.choices_for_year_field import next_five_years
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill


class YearDropdownField(forms.TypedChoiceField):
    def __init__(self, *args, empty_label=_("Year"), **kwargs):
        default_choice = [("", empty_label)]
        choices = default_choice + [(year, str(year)) for year in next_five_years()]
        super().__init__(*args, **kwargs, choices=choices)


class HouseBaseBillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            verbose_name = self.Meta.model._meta.get_field(field_name).verbose_name

            if field_name == "month":
                field.widget.choices = [('', verbose_name)] + list(field.widget.choices)[1:]

            field.widget.attrs['placeholder'] = verbose_name
            field.label = False


class HouseMonthlyBillForm(HouseBaseBillForm):
    year = YearDropdownField(label=_("Year"))

    class Meta:
        model = HouseMonthlyBill
        fields = ("month", "year", "electricity_common",
                  "electricity_lift", "internet", "maintenance_lift",
                  "fee_cleaner", "fee_manager_and_cashier", "repairs",
                  "others")


class HouseOtherBillForm(HouseBaseBillForm):
    year = YearDropdownField(label=_("Year"))

    class Meta:
        model = HouseOtherBill
        fields = ("month", "year", "comment", "total_amount")
