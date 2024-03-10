from django.contrib import admin
from django.contrib.auth import admin as auth_admin, get_user_model

from house_manager.accounts.forms import HouseManagerUserCreationForm, HouseManagerUserChangeForm

UserModel = get_user_model()


@admin.register(UserModel)
class AppUserAdmin(auth_admin.UserAdmin):
    model = UserModel
    add_form = HouseManagerUserCreationForm
    form = HouseManagerUserChangeForm

    list_display = ("email", "is_staff", "is_superuser", "pk")
    search_fields = ("email",)
    ordering = ("pk",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ()}),
        ("Permissions", {"fields": ("is_active", "is_staff", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
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

    def full_name(self, obj):
        return obj.profile.full_name if obj.profile.full_name else ""

