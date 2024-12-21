from django.contrib import admin

from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill


@admin.register(ClientMonthlyBill)
class ClientMonthlyBillAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    list_display = ("house", "client", "month", "year", "electricity_common",
                    "electricity_lift", "internet", "maintenance_lift",
                    "fee_cleaner", "fee_manager", "fee_cashier", "repairs",
                    "others", "total_amount")

    ordering = ("house", "client__apartment", "-year", "month")

    list_filter = ("year", "month")

    search_fields = ["house__town", "house__address", "house__building_number", "client__family_name"]
    search_help_text = "Search by house details or family name"


@admin.register(ClientOtherBill)
class ClientOtherBillBillAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    list_display = ("house", "client", "month", "year", "comment", "total_amount")

    ordering = ("house", "client__apartment", "-year", "month")

    list_filter = ("year", "month")

    search_fields = ["house__town", "house__address", "house__building_number", "client__family_name"]
    search_help_text = "Search by house details or family name"
