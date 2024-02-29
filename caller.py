import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "house_manager.settings")
django.setup()

# from house_manager.houses.models import House
# from django.db.models import Sum, Q
#
#
# def total_people(house_id):
#     q = Q(id=house_id)
#
#     people = (
#         House.objects
#         .prefetch_related('clients')
#         .filter(q)
#         .aggregate(total_people=Sum('clients__number_of_people'))
#     )
#
#     return people['total_people']
#
#
# def total_people_using_lift(house_id):
#     query = Q(id=house_id) & Q(clients__is_using_lift=True)
#
#     people = (
#         House.objects
#         .prefetch_related('clients')
#         .filter(query)
#         .aggregate(total_people=Sum('clients__number_of_people'))
#     )
#
#     return people['total_people']
#
#
# print(total_people(1))
# print(total_people_using_lift(1))
