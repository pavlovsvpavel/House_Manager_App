from django.db import models

from house_manager.accounts.models import UserProfile
from house_manager.common.mixins import TimeStampModel
from house_manager.common.validators import validate_char_field
from house_manager.houses.managers import SingleHouseManager


class House(TimeStampModel):
    town = models.CharField(
        max_length=20,
        validators=[
            validate_char_field,
        ]
    )

    address = models.CharField(
        max_length=100,
    )

    building_number = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    entrance = models.CharField(
        max_length=1,
    )

    owner = models.ForeignKey(
        to=UserProfile,
        on_delete=models.CASCADE,
        related_name='houses'
    )

    objects = SingleHouseManager()

    def __str__(self):
        return (f"{self.town}, {self.address}, "
                f"{self.building_number}, {self.entrance}")

