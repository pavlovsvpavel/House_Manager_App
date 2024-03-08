# from house_manager.accounts.models import Profile
#
#
# class GetProfileMixin:
#
#     @staticmethod
#     def get_profile():
#         return Profile.objects.first()
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         profile = self.get_profile()
#
#         if profile is None:
#             context["profile"] = False
#
#         else:
#             context["profile"] = True
#
#         return context
from django.contrib.auth import mixins as auth_mixins


class OwnerRequiredMixin(auth_mixins.AccessMixin):
    """Verify that the current user is owner of this profile."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.pk != kwargs.get("pk", None):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
