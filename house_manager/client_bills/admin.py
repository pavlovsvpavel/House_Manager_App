from django.contrib import admin
from import_export.admin import ExportMixin
from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill


@admin.register(ClientMonthlyBill)
class ClientMonthlyBillAdmin(CheckLoggedInUserModelInstancesMixin, ExportMixin, admin.ModelAdmin):
    list_display = (
        "house", "client", "month", "year", "electricity_common",
        "electricity_lift", "internet", "maintenance_lift",
        "fee_cleaner", "fee_manager", "fee_cashier", "repairs",
        "others", "total_amount", "amount_old_debts",
    )

    ordering = (
        "house", "client__apartment", "-year", "month",
    )

    list_filter = ("year", "month",)

    search_fields = (
        "house__town", "house__address",
        "house__building_number", "client__family_name",
    )
    search_help_text = "Search by house details or family name"

    fieldsets = (
        (None, {
            "fields": (
                "house", "client", "month", "year",
                "electricity_common", "electricity_lift", "internet",
                "maintenance_lift", "fee_cleaner", "fee_manager",
                "fee_cashier", "repairs", "others", "is_paid", "user",
            )
        }),
        ("Amount without old debts", {
            "fields": ("total_amount",)
        }),
        ("Old debts", {
            "fields": ("amount_old_debts",)
        }),
    )

    readonly_fields = ("total_amount", "house", "client", "month", "year",)


@admin.register(ClientOtherBill)
class ClientOtherBillBillAdmin(CheckLoggedInUserModelInstancesMixin, ExportMixin, admin.ModelAdmin):
    list_display = (
        "house", "client", "month", "year",
        "comment", "total_amount",
    )

    ordering = (
        "house", "client__apartment", "-year", "month",
    )

    list_filter = ("year", "month")

    search_fields = (
        "house__town", "house__address", "house__building_number",
        "client__family_name",
    )
    search_help_text = "Search by house details or family name"

    fieldsets = (
        (None, {
            "fields": (
                "house", "client", "month", "year",
                "comment", "is_paid", "user",
            )
        }),
        ("Amount", {
            "fields": ("total_amount",)
        }),
    )

    readonly_fields = ("total_amount", "house", "client", "month", "year",)
