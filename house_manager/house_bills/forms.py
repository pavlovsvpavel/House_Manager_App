from django import forms
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill


class HouseBaseBillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            verbose_name = self.Meta.model._meta.get_field(field_name).verbose_name

            if field_name in ["month", "year", "type_of_bill"]:
                field.widget.choices = [('', verbose_name)] + list(field.widget.choices)[1:]

            field.widget.attrs['placeholder'] = verbose_name
            field.label = False


class HouseMonthlyBillForm(HouseBaseBillForm):
    class Meta:
        model = HouseMonthlyBill
        fields = ("month", "year", "electricity_common",
                  "electricity_lift", "internet", "maintenance_lift",
                  "fee_cleaner", "fee_manager_and_cashier", "fee_cashier", "repairs",
                  "others")


class HouseOtherBillForm(HouseBaseBillForm):
    class Meta:
        model = HouseOtherBill
        fields = ("month", "year", "comment", "type_of_bill", "total_amount")
