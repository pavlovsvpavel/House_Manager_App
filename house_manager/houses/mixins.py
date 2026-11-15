from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from house_manager.houses.models import House


class GetHouseAndUserMixin:
    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        house_id = self.request.session.get("selected_house")

        if not house_id:
            raise PermissionDenied("No house selected.")

        # The house must belong to the logged-in user — the session value is
        # not a sufficient proof of ownership on its own.
        house = get_object_or_404(House, pk=house_id, user=self.request.user)
        form.instance.house = house
        form.instance.user = self.request.user

        return form
