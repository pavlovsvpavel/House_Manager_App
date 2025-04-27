from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import Http404
from house_manager.houses.models import House


def get_current_house_id(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        selected_house_id = kwargs['pk']

        if not selected_house_id:
            raise Http404("House does not exist.")

        try:
            selected_house = House.objects.select_related('user').get(id=selected_house_id)
            request.selected_house = selected_house
            request.session['selected_house'] = selected_house.pk

            if selected_house.user_id != request.user.id:
                raise PermissionDenied("You are not the owner of this house.")

            return view_func(request, *args, **kwargs)

        except House.DoesNotExist:
            raise Http404("House does not exist.")

    return wrapper
