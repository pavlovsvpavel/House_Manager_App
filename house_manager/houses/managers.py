from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce


class SingleHouseManager(models.Manager):
    def _base_house_query(self, house_id):
        return self.get_queryset().filter(id=house_id)

    def total_people(self, house_id):
        return (
            self._base_house_query(house_id)
            .aggregate(total_people=Coalesce(
                Sum('clients__number_of_people'), 0))
            ['total_people']
        )

    def total_people_using_lift(self, house_id):
        return (
            self._base_house_query(house_id)
            .filter(clients__is_using_lift=True)
            .aggregate(total_people=Coalesce(
                Sum('clients__number_of_people'), 0))
            ['total_people']
        )

    def total_apartments(self, house_id):
        return (
            self._base_house_query(house_id)
            .aggregate(total_apartments=Coalesce(
                Count('clients__apartment', distinct=True), 0))
            ['total_apartments']
        )

    def uninhabitable_apartments(self, house_id):
        return (
            self._base_house_query(house_id)
            .filter(clients__is_inhabitable=False)
            .aggregate(uninhabitable_apartments=Coalesce(
                Count('clients__apartment', distinct=True), 0))
            ['uninhabitable_apartments']
        )

