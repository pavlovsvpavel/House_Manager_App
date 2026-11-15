from django.urls import path

from house_manager.house_bills.views import (
    HouseMonthlyBillCreateView,
    CurrentHouseMonthlyBillDetailView,
    HouseMonthlyBillEditView, HouseOtherBillCreateView,
    CurrentHouseOtherBillDetailView, HouseOtherBillEditView,
    ReportMonthlyBillView, ReportOtherBillView,
    HouseFixedMonthlyBillView
)

# Mounted at: houses/<int:house_pk>/bills/
urlpatterns = (
    path("monthly/create/", HouseMonthlyBillCreateView.as_view(), name="create_house_bills"),
    path("monthly/", CurrentHouseMonthlyBillDetailView.as_view(), name="list_house_bills"),
    path("monthly/<int:pk>/edit/", HouseMonthlyBillEditView.as_view(), name="edit_house_bills"),
    path("fixed/create/", HouseFixedMonthlyBillView.as_view(), name="create_fixed_bill"),
    path("other/create/", HouseOtherBillCreateView.as_view(), name="create_other_bill"),
    path("other/", CurrentHouseOtherBillDetailView.as_view(), name="list_other_house_bills"),
    path("other/<int:pk>/edit/", HouseOtherBillEditView.as_view(), name="edit_other_house_bills"),
    path("reports/monthly/", ReportMonthlyBillView.as_view(), name="reports_bills"),
    path("reports/other/", ReportOtherBillView.as_view(), name="reports_other_bills"),
)
