from django.urls import path

from house_manager.houses.views import HouseCreateView, HouseListClientsDetailsView, HouseEditView

urlpatterns = (
    path("create/", HouseCreateView.as_view(), name="create_house"),
    path("<int:pk>/list-clients/", HouseListClientsDetailsView.as_view(), name="list_clients_house"),
    path("<int:pk>/edit/", HouseEditView.as_view(), name="edit_house"),
)
