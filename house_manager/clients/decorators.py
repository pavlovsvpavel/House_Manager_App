from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import Http404
from house_manager.clients.models import Client


def get_current_client_id(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        selected_client_id = kwargs['pk']

        if not selected_client_id:
            raise Http404("Client does not exist.")

        try:
            selected_client = Client.objects.get(id=selected_client_id)
            request.selected_client = selected_client
            request.session['selected_client'] = selected_client.pk

            if selected_client.user_id != request.user.id:
                raise PermissionDenied("You are not the owner of this house.")

            return view_func(request, *args, **kwargs)

        except Client.DoesNotExist:
            raise Http404("Client does not exist.")

    return wrapper
