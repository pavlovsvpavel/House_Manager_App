from django import forms

from house_manager.house_bills.helpers.choices_for_year_field import next_five_years
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill


class YearDropdownField(forms.TypedChoiceField):
    def __init__(self, *args, empty_label='---------', **kwargs):
        default_choice = [('', empty_label)]
        choices = default_choice + [(year, str(year)) for year in next_five_years()]
        super().__init__(*args, **kwargs, choices=choices)


class HouseMonthlyBillForm(forms.ModelForm):
    year = YearDropdownField(label='Year')

    class Meta:
        model = HouseMonthlyBill
        fields = ("month", "year", "electricity_common",
                  "electricity_lift", "internet", "maintenance_lift",
                  "fee_cleaner", "fee_manager_and_cashier", "repairs",
                  "others")


class HouseOtherBillForm(forms.ModelForm):
    year = YearDropdownField(label='Year')

    class Meta:
        model = HouseOtherBill
        fields = ("month", "year", "comment", "total_amount")
