from django.core.exceptions import ValidationError


def validate_char_field(value):
    if not value.isalpha():
        raise ValidationError('Field should contains only letters')


def validate_phone_number(value):
    if not value.isdigit():
        raise ValidationError('Phone number should contains only digits')

    elif len(value) != 10:
        raise ValidationError('Phone number should be exactly 10 digits')
