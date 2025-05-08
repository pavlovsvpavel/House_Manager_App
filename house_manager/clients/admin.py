from django.contrib import admin

from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.clients.models import Client


@admin.register(Client)
class ClientAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    list_display = (
        "family_name", "floor", "apartment",
        "number_of_people", "is_using_lift", "is_occupied",
        "is_inhabitable", "house", "id",
    )

    list_filter = ("is_using_lift", "is_occupied", "is_inhabitable",)

    ordering = ("house", "apartment",)

    search_fields = ("family_name",)
    search_help_text = "Search by family name"

    fieldsets = (
        (None, {
            'fields': (
                "family_name", "floor", "apartment",
                "number_of_people", "is_using_lift",
                "is_occupied", "is_inhabitable", "house", "user",
            )
        }),
        ("Date", {
            "fields": (
                "created_on", "updated_on",
            )
        }),
    )

    readonly_fields = ("created_on", "updated_on", "house",)
