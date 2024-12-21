from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

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
        verbose_name=_("Family Name"),
    )

    floor = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name=_("Floor"),
    )

    apartment = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name=_("Apartment"),
    )

    number_of_people = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name=_("Number of people"),
    )

    is_using_lift = models.BooleanField(
        blank=False,
        null=False,
        default=True,
        verbose_name=_("Using lift"),
    )

    is_occupied = models.BooleanField(
        blank=False,
        null=False,
        default=True,
        verbose_name=_("Occupied"),
    )

    is_inhabitable = models.BooleanField(
        blank=False,
        null=False,
        default=True,
        verbose_name=_("Inhabitable"),
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

