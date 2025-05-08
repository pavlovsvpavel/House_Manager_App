from django.urls import path

from house_manager.accounts.views import (
    LogInUserView, RegisterUserView,
    logout_user, ProfileDetailsView,
    ProfileUpdateView, ProfileDeleteView, ProfilePasswordChange, ProfilePasswordSet
)

urlpatterns = (
    path("identity/login/", LogInUserView.as_view(), name="login_user"),
    path("identity/register/", RegisterUserView.as_view(), name="register_user"),
    path("logout/", logout_user, name="logout_user"),
    path("profile/details/<int:pk>/", ProfileDetailsView.as_view(), name="details_profile"),
    path("profile/edit/<int:pk>/", ProfileUpdateView.as_view(), name="edit_profile"),
    path("profile/delete/<int:pk>/", ProfileDeleteView.as_view(), name="delete_profile"),
    path("profile/password-change/<int:pk>/", ProfilePasswordChange.as_view(), name="change_password"),
    path("profile/password-set/<int:pk>/", ProfilePasswordSet.as_view(), name="set_password"),
)
