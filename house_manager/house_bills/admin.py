from django.contrib import admin
from house_manager.house_bills.models import HouseMonthlyBill


@admin.register(HouseMonthlyBill)
class HouseMonthlyBillAdmin(admin.ModelAdmin):
    list_display = ("house", "month", "year", "electricity_common",
                    "electricity_lift", "internet", "maintenance_lift",
                    "fee_cleaner", "fee_manager_and_cashier", "repairs",
                    "others", "total_amount")

    ordering = ("house", "-year", "month")

