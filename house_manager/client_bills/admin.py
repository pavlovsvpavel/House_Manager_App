from django.contrib import admin
from django_admin_multi_select_filter.filters import MultiSelectFieldListFilter
from import_export import resources, fields
from import_export.admin import ExportMixin
from house_manager.accounts.mixins import CheckLoggedInUserModelInstancesMixin
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill


class ClientMonthlyBillResource(resources.ModelResource):
    house = fields.Field(column_name='House')
    client = fields.Field(column_name='Client')
    total_amount = fields.Field(attribute='total_amount', column_name='Total Amount, EUR')
    amount_old_debts = fields.Field(attribute='amount_old_debts', column_name='Amount Old Debts, EUR')
    apartment = fields.Field(attribute='client__apartment', column_name='Apartment')
    floor = fields.Field(attribute='client__floor', column_name='Floor')
    month = fields.Field(attribute='month', column_name='Month')
    year = fields.Field(attribute='year', column_name='Year')

    class Meta:
        model = ClientMonthlyBill
        fields = (
            "client", "house", "floor", "apartment", "month", "year",
            "electricity_common", "electricity_lift", "internet",
            "maintenance_lift", "fee_cleaner", "fee_manager",
            "fee_cashier", "repairs", "others", "total_amount",
            "amount_old_debts", "is_paid",
        )
        export_order = fields

    def dehydrate_house(self, obj):
        return str(obj.house) if obj.house else ""

    def dehydrate_client(self, obj):
        return str(obj.client) if obj.client else ""

    def dehydrate_month(self, obj):
        return obj.get_month_display() if obj.month else ""


@admin.register(ClientMonthlyBill)
class ClientMonthlyBillAdmin(CheckLoggedInUserModelInstancesMixin, ExportMixin, admin.ModelAdmin):
    resource_classes = [ClientMonthlyBillResource]
    list_display = (
        "client", "client__floor", "client__apartment", "month", "year", "electricity_common",
        "electricity_lift", "internet", "maintenance_lift",
        "fee_cleaner", "fee_manager", "fee_cashier", "repairs",
        "others", "total_amount", "amount_old_debts", "house",
    )

    ordering = (
        "-year", "month", "client__floor", "client__apartment", "house",
    )

    list_filter = (
        ("year", MultiSelectFieldListFilter),
        ("month", MultiSelectFieldListFilter),
    )

    search_fields = (
        "house__town", "house__address",
        "house__building_number", "client__family_name",
    )
    search_help_text = "Search by house details or family name"

    fieldsets = (
        (None, {
            "fields": (
                "client", "month", "year",
                "electricity_common", "electricity_lift", "internet",
                "maintenance_lift", "fee_cleaner", "fee_manager",
                "fee_cashier", "repairs", "others", "is_paid", "user", "house",
            )
        }),
        ("Amount without old debts", {
            "fields": ("total_amount",)
        }),
        ("Old debts", {
            "fields": ("amount_old_debts",)
        }),
        ("Signature", {
            "fields": ("signature",)
        }),
    )

    readonly_fields = ("total_amount", "house", "client", "month", "year",)


@admin.register(ClientOtherBill)
class ClientOtherBillBillAdmin(CheckLoggedInUserModelInstancesMixin, ExportMixin, admin.ModelAdmin):
    list_display = (
        "house", "client", "client__apartment", "month", "year",
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
        ("Signature", {
            "fields": ("signature",)
        }),
    )

    readonly_fields = ("total_amount", "house", "client", "month", "year",)
