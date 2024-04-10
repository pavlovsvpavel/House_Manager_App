from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_SIZE = 3 * 1024 * 1024


def validate_profile_picture_size(value):
    if not value:
        return
    if value.size > MAX_SIZE:
        raise ValidationError(_('The maximum file size should not exceed 3MB'))


def validate_image_file(value):
    if value and not value.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        raise ValidationError(_('Unsupported file type. Please upload an image file (.jpg, .jpeg, .png, .gif)'))
