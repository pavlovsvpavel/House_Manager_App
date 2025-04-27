from django.urls import path
from house_manager.house_bills.views import (
    HouseMonthlyBillCreateView,
    CurrentHouseMonthlyBillDetailView,
    HouseMonthlyBillEditView, HouseOtherBillCreateView,
    CurrentHouseOtherBillDetailView, HouseOtherBillEditView, ReportMonthlyBillView, ReportOtherBillView
)

urlpatterns = (
    path("create-bill/", HouseMonthlyBillCreateView.as_view(), name="create_house_bills"),
    path("list-bills/<int:pk>/", CurrentHouseMonthlyBillDetailView.as_view(), name="list_house_bills"),
    path("edit-bills/<int:pk>/", HouseMonthlyBillEditView.as_view(), name="edit_house_bills"),
    path("create-other-bill/", HouseOtherBillCreateView.as_view(), name="create_other_bill"),
    path("list-other-bills/<int:pk>/", CurrentHouseOtherBillDetailView.as_view(), name="list_other_house_bills"),
    path("edit-other-bills/<int:pk>/", HouseOtherBillEditView.as_view(), name="edit_other_house_bills"),
    path('reports-bills/<int:pk>/', ReportMonthlyBillView.as_view(), name='reports_bills'),
    path('reports-other-bills/<int:pk>/', ReportOtherBillView.as_view(), name='reports_other_bills'),
)
