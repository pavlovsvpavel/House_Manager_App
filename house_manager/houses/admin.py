from django.contrib import admin
from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.houses.models import House, HouseCalculationsOptions


@admin.register(House)
class HouseAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    list_display = (
        "town", "address", "building_number",
        "entrance", "id",
    )

    ordering = ("id",)

    search_fields = (
        "town", "address", "building_number",
    )
    search_help_text = "Search by town, address or building_number"

    fieldsets = (
        (None, {
            'fields': ("town", "address", "building_number", "entrance", "money_balance", "user")
        }),
        ("Date", {
            "fields": (
                "created_on", "updated_on",
            )
        }),
    )

    readonly_fields = ("created_on", "updated_on",)


@admin.register(HouseCalculationsOptions)
class HouseCalculationsOptionsAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.fields]
