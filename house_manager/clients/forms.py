from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from house_manager.clients.models import Client


class ClientBaseForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied",
                  "is_inhabitable")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field_tooltips = {
            'is_using_lift': _('Mark this option, if the residents in this apartment are using lift'),
            'is_occupied': _('Mark this option, if this apartment is currently occupied'),
            'is_inhabitable': _('Mark this option, if this apartment is permanently inhabitable'),
        }

        for field_name, field in self.fields.items():
            verbose_name = self.Meta.model._meta.get_field(field_name).verbose_name

            if field_name in field_tooltips:
                field.label_suffix = ''
                field.help_text = mark_safe(
                    f'<span class="tooltip-icon" data-tooltip="{field_tooltips[field_name]}"><i class="fa-solid fa-circle-info"></i></span>'
                )
                field.label = mark_safe(f'{verbose_name} {field.help_text}')


class ClientCreateForm(ClientBaseForm):
    pass


class ClientEditForm(ClientBaseForm):
    pass
