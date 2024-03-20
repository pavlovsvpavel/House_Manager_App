from django.contrib.auth import mixins as auth_mixins
from django.core.exceptions import PermissionDenied


class OwnerRequiredMixin(auth_mixins.AccessMixin):
    """Verify that the current user is owner of this profile."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.pk != kwargs.get("pk", None):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CheckForLoggedInUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to access this view.")
        return super().dispatch(request, *args, **kwargs)
