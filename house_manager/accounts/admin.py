from django.contrib import admin

from house_manager.accounts.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "password")
