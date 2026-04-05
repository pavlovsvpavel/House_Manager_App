from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_char_field(value):
    allowed_symbols = " ()/-"

    if not all(char.isalpha() or char in allowed_symbols for char in value):
        raise ValidationError(_("Field should contain only letters, spaces, (), /, and -"))

    has_letter = any(char.isalpha() for char in value)
    if not has_letter:
        raise ValidationError(_("Field must contain at least one letter"))


def validate_phone_number(value):
    if not value.isdigit():
        raise ValidationError(_("Phone number should contains only digits"))

    elif len(value) != 10:
        raise ValidationError(_("Phone number should be exactly 10 digits"))
