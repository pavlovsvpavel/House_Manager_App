from django.contrib import admin

from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.houses.models import House


@admin.register(House)
class HouseAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    list_display = ["town", "address", "building_number", "entrance", "id"]

    ordering = ["id"]

    search_fields = ["town", "address", "building_number"]
    search_help_text = "Search by town, address or building_number"
