from functools import wraps

from django.core.exceptions import PermissionDenied
from house_manager.clients.models import Client


def get_current_client_id(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        selected_client_id = kwargs['pk']
        if selected_client_id:
            try:
                selected_client = Client.objects.get(id=selected_client_id)
            except Client.DoesNotExist:
                raise PermissionDenied("Client does not exist.")

            if selected_client.user == request.user:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied("You are not the owner of this house.")
        else:
            raise PermissionDenied("Client does not exist.")
    return wrapper
