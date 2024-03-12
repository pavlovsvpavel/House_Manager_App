from django.urls import path

from house_manager.clients.views import ClientCreateView
from house_manager.house_bills.views import HouseMonthlyBillCreateView
from house_manager.houses.views import HouseCreateView, HouseEditView, HouseDetailsView, HouseClientsDetailsView, \
    HouseDeleteView, StoreSelectedHouseView

urlpatterns = (
    path("store_selected_house/", StoreSelectedHouseView.as_view(), name="store_selected_house"),
    path("create/", HouseCreateView.as_view(), name="create_house"),
    path("<int:pk>/details/", HouseDetailsView.as_view(), name="details_house"),
    path("<int:pk>/edit/", HouseEditView.as_view(), name="edit_house"),
    path("<int:pk>/clients/", HouseClientsDetailsView.as_view(), name="list_house_clients"),
    path("<int:pk>/clients/create/", ClientCreateView.as_view(), name="create_client"),
    path("<int:pk>/house-bill/create/", HouseMonthlyBillCreateView.as_view(), name="create_house_bills"),
    path("<int:pk>/delete/", HouseDeleteView.as_view(), name="delete_house"),
)
