from django.urls import path

from house_manager.house_bills.views import (
    HouseMonthlyBillCreateView,
    CurrentHouseMonthlyBillDetailView,
    HouseMonthlyBillEditView
)

urlpatterns = (
    path("create/", HouseMonthlyBillCreateView.as_view(), name="create_house_bills"),
    path("<int:pk>/list/", CurrentHouseMonthlyBillDetailView.as_view(), name="list_house_bills"),
    # path("<int:pk>/details/", HouseMonthlyBillDetailView.as_view(), name="details_house_bills"),
    path("<int:pk>/details/", HouseMonthlyBillEditView.as_view(), name="details_house_bills"),
)
