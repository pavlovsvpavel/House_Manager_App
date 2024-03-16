from django.contrib.auth import get_user_model
from django.db import models

from house_manager.accounts.models import Profile
from house_manager.common.mixins import TimeStampModel
from house_manager.common.validators import validate_char_field
from house_manager.houses.managers import SingleHouseManager

UserModel = get_user_model()


class House(TimeStampModel):
    MAX_TOWN_LENGTH = 20
    MAX_ADDRESS_LENGTH = 100
    MAX_ENTRANCE_LENGTH = 2

    town = models.CharField(
        max_length=MAX_TOWN_LENGTH,
        validators=[
            validate_char_field,
        ],
        blank=False,
        null=False,
    )

    address = models.CharField(
        max_length=MAX_ADDRESS_LENGTH,
        blank=False,
        null=False,
    )

    building_number = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    entrance = models.CharField(
        max_length=MAX_ENTRANCE_LENGTH,
        blank=False,
        null=False,
    )

    money_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=False,
        null=False,
        default=0,
    )

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
    )

    objects = SingleHouseManager()

    def __str__(self):
        return (f"{self.town}, {self.address}, "
                f"{self.building_number}, {self.entrance}")
