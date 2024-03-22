from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_SIZE = 1 * 1024 * 1024


def validate_profile_picture_size(value):
    if value.size > MAX_SIZE:
        raise ValidationError(_('The maximum file size should not exceed 1MB'))
