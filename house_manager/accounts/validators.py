from django.core.exceptions import ValidationError

MAX_SIZE = 3 * 1024 * 1024


def validate_profile_picture_size(value):
    if value.size > MAX_SIZE:
        raise ValidationError('The maximum file size should not exceed 3MB')
