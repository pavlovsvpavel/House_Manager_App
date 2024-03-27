from django.urls import path
from house_manager.common.views import IndexView, DashboardView, about_view

urlpatterns = (
    path("", IndexView.as_view(), name="index"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("about/", about_view, name="about"),
)

