from django.urls import path

from house_manager.accounts.views import (
    LogInUserView, RegisterUserView,
    logout_user, ProfileDetailsView,
    ProfileUpdateView, ProfileDeleteView
)

urlpatterns = (
    path("identity/login/", LogInUserView.as_view(), name="login_user"),
    path("identity/register/", RegisterUserView.as_view(), name="register_user"),
    path("logout/", logout_user, name="logout_user"),
    path("profile/<int:pk>/details/", ProfileDetailsView.as_view(), name="details_profile"),
    path("profile/<int:pk>/edit/", ProfileUpdateView.as_view(), name="edit_profile"),
    path("profile/<int:pk>/delete/", ProfileDeleteView.as_view(), name="delete_profile"),
)
