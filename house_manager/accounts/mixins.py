from django.contrib.auth import mixins as auth_mixins
from django.core.exceptions import PermissionDenied

from house_manager.clients.models import Client
from house_manager.houses.models import House


class OwnerRequiredMixin(auth_mixins.AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.pk != kwargs.get("pk", None):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CheckForLoggedInUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to access this view.")
        return super().dispatch(request, *args, **kwargs)


class CheckLoggedInUserModelInstancesMixin:
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset

    def get_form(self, request, obj=None, **kwargs):
        """
        Prefill the user field with the logged-in user's email and make it read-only.
        Also, limit the house and/or client fields to only show houses and/or clients owned by the logged-in user.
        """
        form = super().get_form(request, obj, **kwargs)

        if not request.user.is_superuser:
            form.base_fields['user'].initial = request.user
            form.base_fields['user'].disabled = True

            if 'house' in form.base_fields:
                form.base_fields['house'].queryset = House.objects.filter(user=request.user)
            if 'client' in form.base_fields:
                form.base_fields['client'].queryset = Client.objects.filter(user=request.user)
        else:
            # Superuser don't have limitations with prefilled fields
            form = super().get_form(request, obj, **kwargs)

        return form

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.user = request.user
        super().save_model(request, obj, form, change)