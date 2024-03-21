from django.urls import path

from house_manager.clients.views import (
    ClientCreateView, ClientDetailView,
    ClientEditView, ClientDeleteView
)

urlpatterns = (
    path("create/", ClientCreateView.as_view(), name="create_client"),
    path("<int:pk>/details/", ClientDetailView.as_view(), name="details_client"),
    path("<int:pk>/edit/", ClientEditView.as_view(), name="edit_client"),
    path("<int:pk>/delete/", ClientDeleteView.as_view(), name="delete_client"),
)
