from django.core.exceptions import PermissionDenied
from django.http import Http404
from house_manager.clients.models import Client


class ClientOwnershipMixin:
    """
    Loads the client from the URL (``client_pk``) and verifies that it
    belongs to the logged-in user and to the house in the URL (``house_pk``).

    Replaces the old session-based ``selected_client`` pattern: ownership is
    derived from the URL on every request, so foreign clients return 404 and
    no mutable "current client" state lives in the session.
    """

    selected_client = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to access this view.")

        try:
            self.selected_client = Client.objects.get(
                pk=kwargs["client_pk"],
                user=request.user,
            )
        except Client.DoesNotExist:
            # 404 — never confirm that a foreign client exists.
            raise Http404("Client does not exist.")

        if self.selected_client.house_id != kwargs.get("house_pk"):
            raise Http404("Client does not exist.")

        return super().dispatch(request, *args, **kwargs)
