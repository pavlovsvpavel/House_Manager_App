from django.contrib import admin
from import_export.admin import ExportMixin
from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill


@admin.register(HouseMonthlyBill)
class HouseMonthlyBillAdmin(CheckLoggedInUserModelInstancesMixin, ExportMixin, admin.ModelAdmin):
    list_display = (
        "house", "month", "year", "electricity_common",
        "electricity_lift", "internet", "maintenance_lift",
        "fee_cleaner", "fee_manager", "fee_cashier", "repairs",
        "others", "total_amount",
    )

    ordering = ("house", "-year", "month")

    list_filter = ("year", "month")

    search_fields = (
        "house__town", "house__address",
        "house__building_number",
    )
    search_help_text = "Search by house details"

    fieldsets = (
        (None, {
            'fields': (
                "house", "month", "year",
                "electricity_common", "electricity_lift", "internet",
                "maintenance_lift", "fee_cleaner", "fee_manager",
                "fee_cashier", "repairs", "others", "is_paid", "user",
            )
        }),
        ("Amount", {
            'fields': ("total_amount",)
        }),
    )

    readonly_fields = ("total_amount","house", "month", "year")


@admin.register(HouseOtherBill)
class HouseOtherBillBillAdmin(CheckLoggedInUserModelInstancesMixin, ExportMixin, admin.ModelAdmin):
    list_display = (
        "type_of_bill", "house", "month",
        "year", "comment", "total_amount",
    )

    ordering = ("house", "-year", "month",)

    list_filter = ("year", "month", "type_of_bill",)

    search_fields = (
        "house__town", "house__address",
        "house__building_number",
    )
    search_help_text = "Search by house details"

    fieldsets = (
        (None, {
            'fields': (
                "type_of_bill", "house", "month",
                "year", "comment", "is_paid", "user",
            )
        }),
        ("Amount", {
            'fields': ("total_amount",)
        }),
    )

    readonly_fields = ("total_amount", "house", "month", "year", "type_of_bill",)
