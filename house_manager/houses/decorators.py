from functools import wraps
from django.http import Http404
from house_manager.houses.models import House


def get_current_house_id(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        selected_house_id = kwargs['pk']
        if selected_house_id:
            try:
                selected_house = House.objects.get(id=selected_house_id)
            except House.DoesNotExist:
                raise Http404("House does not exist.")

            if selected_house.user == request.user:
                return view_func(request, *args, **kwargs)
            else:
                raise Http404("You are not the owner of this house.")
        else:
            raise Http404("House does not exist.")
    return wrapper
