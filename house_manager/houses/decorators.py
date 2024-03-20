from functools import wraps

from django.http import Http404
from django.shortcuts import redirect
from house_manager.houses.models import House


def get_current_house_instance(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            selected_house_id = kwargs['pk']
            if selected_house_id:
                try:
                    selected_house = House.objects.get(id=selected_house_id)
                    return view_func(request, selected_house=selected_house, *args, **kwargs)
                except House.DoesNotExist:
                    raise Http404()
        return redirect('login_user')
    return wrapper
