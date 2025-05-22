from django import forms
from django.utils.translation import gettext_lazy as _
from house_manager.houses.models import House, HouseCalculationsOptions


class HouseBaseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ("town", "address", "building_number", "entrance", "money_balance")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            verbose_name = self.Meta.model._meta.get_field(field_name).verbose_name
            field.widget.attrs["placeholder"] = verbose_name
            field.label = ''


class HouseCreateForm(HouseBaseForm):
    money_balance = forms.CharField(
        label=_("Current balance, BGN"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "title": _("Enter house's current available amount")
            }
        )
    )


class HouseEditForm(HouseBaseForm):
    pass


class HorizontalCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs = {'class': 'checkbox-grid'}


class HouseCalculationsOptionsEditForm(forms.ModelForm):
    based_on_apartment = forms.MultipleChoiceField(
        required=False,
        widget=HorizontalCheckboxSelectMultiple,
        label=_("Calculations based on apartment:")
    )

    based_on_total_people = forms.MultipleChoiceField(
        required=False,
        widget=HorizontalCheckboxSelectMultiple,
        label=_("Calculations based on total people:")
    )

    class Meta:
        model = HouseCalculationsOptions
        fields = ['based_on_apartment', 'based_on_total_people', 'house', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'house' in self.initial:
            self.instance.house_id = self.initial['house']
        if 'user' in self.initial:
            self.instance.user_id = self.initial['user']

        choices = HouseCalculationsOptions.get_monthly_bill_field_choices()

        self.fields['based_on_apartment'].choices = choices
        self.fields['based_on_total_people'].choices = choices

    def clean(self):
        cleaned_data = super().clean()

        apartment_selected = set(cleaned_data.get('based_on_apartment', []))
        people_selected = set(cleaned_data.get('based_on_total_people', []))

        conflicts = apartment_selected & people_selected

        if conflicts:
            raise forms.ValidationError(
                f"These fields cannot be in both categories: {', '.join(conflicts)}"
            )

        return cleaned_data
