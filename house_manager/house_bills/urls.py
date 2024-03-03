from django.urls import path

from house_manager.house_bills.views import HouseMonthlyBillCreateView

urlpatterns = (
    path("create/", HouseMonthlyBillCreateView.as_view(), name="create_house_bills"),
)
