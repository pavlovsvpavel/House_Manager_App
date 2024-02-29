from django.db import models

from house_manager.common.mixins import TimeStampModel
from house_manager.common.validators import validate_char_field, validate_phone_number


class UserProfile(TimeStampModel):
    username = models.CharField(
        max_length=30,
        unique=True,

        error_messages={
            "unique": "A user with that username already exists",
        }
    )

    first_name = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        validators=[
            validate_char_field
        ],
    )

    last_name = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        validators=[
            validate_char_field
        ],
    )

    password = models.CharField(
        max_length=256,
    )

    email = models.EmailField()

    phone_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[
            validate_phone_number,
        ]
    )

    def __str__(self):
        return f"{self.username}"


