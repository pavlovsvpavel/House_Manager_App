from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_char_field(value):
    if not value.isalpha():
        raise ValidationError(_("Field should contains only letters"))


def validate_phone_number(value):
    if not value.isdigit():
        raise ValidationError(_("Phone number should contains only digits"))

    elif len(value) != 10:
        raise ValidationError(_("Phone number should be exactly 10 digits"))
