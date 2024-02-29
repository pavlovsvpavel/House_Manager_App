from django.urls import path

from house_manager.houses.views import HouseCreateView, HouseDetailsView

urlpatterns = (
    path("create/", HouseCreateView.as_view(), name="create_house"),
    path("<int:pk>/details/", HouseDetailsView.as_view(), name="details_house"),
)
