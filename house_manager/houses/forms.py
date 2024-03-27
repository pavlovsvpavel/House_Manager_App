from django import forms
from django.utils.translation import gettext_lazy as _
from house_manager.houses.models import House


class HouseBaseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ("town", "address", "building_number", "entrance", "money_balance")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            verbose_name = self.Meta.model._meta.get_field(field_name).verbose_name
            field.widget.attrs["placeholder"] = verbose_name
            field.label = False


class HouseCreateForm(HouseBaseForm):
    money_balance = forms.CharField(
        label="Current Balance",
        required=True,
        widget=forms.TextInput(
            attrs={
                "title": _("Enter house's current available amount")
            }
        )
    )


class HouseEditForm(HouseBaseForm):
    pass
