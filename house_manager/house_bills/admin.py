from django.contrib import admin

from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill


@admin.register(HouseMonthlyBill)
class HouseMonthlyBillAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    list_display = ("house", "month", "year", "electricity_common",
                    "electricity_lift", "internet", "maintenance_lift",
                    "fee_cleaner", "fee_manager", "fee_cashier", "repairs",
                    "others", "total_amount")

    ordering = ("house", "-year", "month")

    list_filter = ("year", "month")

    search_fields = ["house__town", "house__address", "house__building_number"]
    search_help_text = "Search by house details"


@admin.register(HouseOtherBill)
class HouseOtherBillBillAdmin(CheckLoggedInUserModelInstancesMixin, admin.ModelAdmin):
    list_display = ("type_of_bill", "house", "month", "year", "comment", "total_amount")

    ordering = ("house", "-year", "month")

    list_filter = ("year", "month", "type_of_bill")

    search_fields = ["house__town", "house__address", "house__building_number"]
    search_help_text = "Search by house details"
