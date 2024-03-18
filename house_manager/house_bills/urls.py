from django.urls import path

from house_manager.house_bills.views import (
    HouseMonthlyBillCreateView,
    CurrentHouseMonthlyBillDetailView,
    HouseMonthlyBillEditView, HouseOtherBillCreateView, CurrentHouseOtherBillDetailView, HouseOtherBillEditView
)

urlpatterns = (
    path("create/", HouseMonthlyBillCreateView.as_view(), name="create_house_bills"),
    path("<int:pk>/list/", CurrentHouseMonthlyBillDetailView.as_view(), name="list_house_bills"),
    path("<int:pk>/details/", HouseMonthlyBillEditView.as_view(), name="edit_house_bills"),
    path("create-other-bill/", HouseOtherBillCreateView.as_view(), name="create_other_bill"),
    path("<int:pk>/other-bills-list/", CurrentHouseOtherBillDetailView.as_view(), name="list_other_house_bills"),
    path("<int:pk>/details-other-bills/", HouseOtherBillEditView.as_view(), name="edit_other_house_bills"),
)
