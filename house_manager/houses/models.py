from django.contrib.auth import get_user_model
from django.db import models

from house_manager.accounts.models import Profile
from house_manager.common.mixins import TimeStampModel
from house_manager.common.validators import validate_char_field
from house_manager.houses.managers import SingleHouseManager

UserModel = get_user_model()


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

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
    )

    objects = SingleHouseManager()

    # def total_people(self, house_id):
    #     query = Q(id=house_id)
    #
    #     people = (
    #         self.objects
    #         .prefetch_related('clients')
    #         .filter(query)
    #         .aggregate(total_people=Sum('clients__number_of_people'))
    #     )
    #
    #     return people['total_people']
    #
    # def total_people_using_lift(self, house_id):
    #     query = Q(id=house_id) & Q(clients__is_using_lift=True)
    #
    #     people = (
    #         self.objects
    #         .prefetch_related('clients')
    #         .filter(query)
    #         .aggregate(total_people=Sum('clients__number_of_people'))
    #     )
    #
    #     return people['total_people']

    def __str__(self):
        return (f"{self.town}, {self.address}, "
                f"{self.building_number}, {self.entrance}")
