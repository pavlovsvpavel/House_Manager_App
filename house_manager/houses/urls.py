from django.urls import path

from house_manager.houses.views import (
    HouseCreateView, HouseEditView,
    HouseDetailsView, HouseClientsDetailsView,
    HouseDeleteView)

urlpatterns = (
    path("create/", HouseCreateView.as_view(), name="create_house"),
    path("<int:pk>/details/", HouseDetailsView.as_view(), name="details_house"),
    path("<int:pk>/edit/", HouseEditView.as_view(), name="edit_house"),
    path("<int:pk>/clients/", HouseClientsDetailsView.as_view(), name="list_house_clients"),
    path("<int:pk>/delete/", HouseDeleteView.as_view(), name="delete_house"),
)
