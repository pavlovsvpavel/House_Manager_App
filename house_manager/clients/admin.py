from django.contrib import admin
from house_manager.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        "family_name", "floor", "apartment",
        "number_of_people", "is_occupied",
        "is_using_lift", "house", "id"
    ]

    list_filter = ["is_using_lift", "is_occupied", "house"]

    ordering = ["house", "apartment"]

    search_fields = ["family_name"]
    search_help_text = "Search by family name"
