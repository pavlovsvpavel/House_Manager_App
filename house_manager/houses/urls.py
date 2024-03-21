from django.urls import path

from house_manager.houses.views import (
    HouseCreateView, HouseEditView,
    HouseDetailView, HouseClientsDetailView,
    HouseDeleteView
)

urlpatterns = (
    path("create/", HouseCreateView.as_view(), name="create_house"),
    path("<int:pk>/details/", HouseDetailView.as_view(), name="details_house"),
    path("<int:pk>/edit/", HouseEditView.as_view(), name="edit_house"),
    path("<int:pk>/clients/", HouseClientsDetailView.as_view(), name="house_clients_list"),
    path("<int:pk>/delete/", HouseDeleteView.as_view(), name="delete_house"),
)
