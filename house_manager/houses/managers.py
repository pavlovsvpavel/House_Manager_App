from django.db import models
from django.db.models import Q, Sum, Count


class SingleHouseManager(models.Manager):

    def total_people(self, house_id):
        query = Q(id=house_id)

        people = (
            self.get_queryset()
            .prefetch_related('clients')
            .filter(query)
            .aggregate(total_people=Sum('clients__number_of_people'))
        )

        return people['total_people'] or 0

    def total_people_using_lift(self, house_id):
        query = Q(id=house_id) & Q(clients__is_using_lift=True)

        people = (
            self.get_queryset()
            .prefetch_related('clients')
            .filter(query)
            .aggregate(total_people=Sum('clients__number_of_people'))
        )

        return people['total_people'] or 0

    def total_apartments(self, house_id):
        query = Q(id=house_id)

        apartments = (
            self.get_queryset()
            .filter(query)
            .aggregate(total_apartments=Count('clients__apartment'))
        )

        return apartments['total_apartments'] or 0
