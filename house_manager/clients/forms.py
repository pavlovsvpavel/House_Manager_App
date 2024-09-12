from django import forms
from house_manager.clients.models import Client


class ClientBaseForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied", "is_inhabitable")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            verbose_name = self.Meta.model._meta.get_field(field_name).verbose_name
            if field_name not in ["is_using_lift", "is_occupied", "is_inhabitable"]:
                field.widget.attrs['placeholder'] = verbose_name
                field.label = False


class ClientCreateForm(ClientBaseForm):
    pass


class ClientEditForm(ClientBaseForm):
    pass
