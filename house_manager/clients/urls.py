from django.urls import path
from house_manager.clients.views import (
    ClientCreateView, ClientDetailView,
    ClientEditView, ClientDeleteView
)

urlpatterns = (
    path("create/", ClientCreateView.as_view(), name="create_client"),
    path("details/<int:pk>/", ClientDetailView.as_view(), name="details_client"),
    path("edit/<int:pk>/", ClientEditView.as_view(), name="edit_client"),
    path("delete/<int:pk>/", ClientDeleteView.as_view(), name="delete_client"),
)
