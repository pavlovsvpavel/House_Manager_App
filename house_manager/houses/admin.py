from django.contrib import admin

from house_manager.houses.models import House


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['town', 'address', 'building_number', 'entrance']
