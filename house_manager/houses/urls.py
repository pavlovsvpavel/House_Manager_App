from django.urls import path
from house_manager.houses.views import (
    HouseCreateView, HouseEditView,
    HouseDetailView, HouseClientsDetailView,
    HouseDeleteView
)

urlpatterns = (
    path("create/", HouseCreateView.as_view(), name="create_house"),
    path("details/<int:pk>/", HouseDetailView.as_view(), name="details_house"),
    path("edit/<int:pk>/", HouseEditView.as_view(), name="edit_house"),
    path("clients/<int:pk>/", HouseClientsDetailView.as_view(), name="house_clients_list"),
    path("delete/<int:pk>/", HouseDeleteView.as_view(), name="delete_house"),
)
