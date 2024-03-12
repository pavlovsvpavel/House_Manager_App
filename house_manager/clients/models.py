from django.contrib.auth import get_user_model
from django.db import models

from house_manager.common.mixins import TimeStampModel
from house_manager.common.validators import validate_char_field
from house_manager.houses.models import House

UserModel = get_user_model()


class Client(TimeStampModel):
    MAX_FAMILY_NAME_LENGTH = 30

    class Meta:
        unique_together = ['apartment', 'house']
        ordering = ['house', 'apartment']

    family_name = models.CharField(
        max_length=MAX_FAMILY_NAME_LENGTH,
        validators=[
            validate_char_field,
        ],
        blank=False,
        null=False,
    )

    floor = models.PositiveIntegerField(
        blank=False,
        null=False,
    )

    apartment = models.PositiveIntegerField(
        blank=False,
        null=False,
    )

    number_of_people = models.PositiveIntegerField(
        blank=False,
        null=False,
    )

    is_using_lift = models.BooleanField(
        default=True,
    )

    is_occupied = models.BooleanField(
        default=True,
    )

    fixed_fee = models.BooleanField(
        default=False,
    )

    house = models.ForeignKey(
        to=House,
        on_delete=models.CASCADE,
        related_name='clients'
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.RESTRICT,
    )

    def __str__(self):
        return self.family_name
