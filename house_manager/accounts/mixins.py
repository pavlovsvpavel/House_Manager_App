from django.contrib.auth import mixins as auth_mixins
from django.core.exceptions import PermissionDenied


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
