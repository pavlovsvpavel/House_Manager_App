from django.contrib import admin

from house_manager.accounts.mixins import CheckUserModelInstancesMixin
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill


@admin.register(ClientMonthlyBill)
class ClientMonthlyBillAdmin(CheckUserModelInstancesMixin, admin.ModelAdmin):
    list_display = ("house", "client", "month", "year", "electricity_common",
                    "electricity_lift", "internet", "maintenance_lift",
                    "fee_cleaner", "fee_manager_and_cashier", "repairs",
                    "others", "total_amount")

    ordering = ("house", "-year", "month")

    list_filter = ("year", "month")

    search_fields = ["house__town", "house__address", "house__building_number"]
    search_help_text = "Search by house details"


@admin.register(ClientOtherBill)
class ClientOtherBillBillAdmin(CheckUserModelInstancesMixin, admin.ModelAdmin):
    list_display = ("house", "client", "month", "year", "comment", "total_amount")

    ordering = ("house", "-year", "month")

    list_filter = ("year", "month")

    search_fields = ["house__town", "house__address", "house__building_number"]
    search_help_text = "Search by house details"
