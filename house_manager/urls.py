from django.contrib import admin
from django.urls import path, include

urlpatterns = (
    path('admin/', admin.site.urls),
    path("", include("house_manager.common.urls")),
    path("accounts/", include("house_manager.accounts.urls")),
    path("houses/", include("house_manager.houses.urls")),
    path("clients/", include("house_manager.clients.urls")),
    path("house-bills/", include("house_manager.house_bills.urls")),
)
