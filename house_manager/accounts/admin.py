from django.contrib import admin
from django.contrib.auth import admin as auth_admin, get_user_model
from django.contrib.sites.models import Site
from house_manager.accounts.forms import (
    HouseManagerUserCreationForm,
    HouseManagerUserChangeForm)

UserModel = get_user_model()


@admin.register(UserModel)
class AppUserAdmin(auth_admin.UserAdmin):
    model = UserModel
    add_form = HouseManagerUserCreationForm
    form = HouseManagerUserChangeForm

    list_display = ("email", "is_superuser", "is_staff", "full_name", "phone_number", "id", "has_set_password")

    search_fields = ("email",)
    search_help_text = "Search by user's email"

    ordering = ("-is_superuser", "email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
        ("Has Set Password", {"fields": ("has_set_password",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        return queryset

    @staticmethod
    def full_name(obj):
        return obj.profile.full_name if obj.profile.full_name else ""

    @staticmethod
    def phone_number(obj):
        return obj.profile.phone_number


admin.site.unregister(Site)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'domain', 'name')
