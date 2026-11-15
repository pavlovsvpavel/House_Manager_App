from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from house_manager.houses.models import House


class HouseOwnershipMixin:
    """
    Loads the house from the URL (``house_pk``) and verifies that it belongs
    to the logged-in user.

    Replaces the old session-based ``selected_house`` pattern: ownership is
    derived from the URL on every request, so foreign houses return 404 and
    no mutable "current house" state lives in the session.
    """

    selected_house = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to access this view.")

        try:
            self.selected_house = House.objects.select_related("user").get(
                pk=kwargs["house_pk"],
                user=request.user,
            )
        except House.DoesNotExist:
            # 404 — never confirm that a foreign house exists.
            raise Http404("House does not exist.")

        return super().dispatch(request, *args, **kwargs)


class GetHouseAndUserMixin:
    """
    For create views nested under ``houses/<house_pk>/...``: assigns the
    ownership-verified house and the logged-in user to the form instance.
    Expects ``HouseOwnershipMixin`` to have loaded ``selected_house``.
    """

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.instance.house = self.selected_house
        form.instance.user = self.request.user
        return form
