from django.contrib import admin

from house_manager.client_bills.models import ClientMonthlyBill


@admin.register(ClientMonthlyBill)
class ClientMonthlyBillAdmin(admin.ModelAdmin):
    list_display = ("house", "client", "month", "year", "electricity_common",
                    "electricity_lift", "internet", "maintenance_lift",
                    "fee_cleaner", "fee_manager_and_cashier", "repairs",
                    "others", "total_amount")

    ordering = ("house", "month", "year")