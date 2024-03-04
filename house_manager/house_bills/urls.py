from django.urls import path

from house_manager.house_bills.views import HouseMonthlyBillCreateView, \
    HouseMonthlyBillDetailView

urlpatterns = (
    path("create/", HouseMonthlyBillCreateView.as_view(), name="create_house_bills"),
    path("<int:pk>/list/", HouseMonthlyBillDetailView.as_view(), name="list_house_bills"),
)
