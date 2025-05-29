from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.clients.decorators import get_current_client_id
from house_manager.clients.forms import ClientCreateForm, ClientEditForm
from house_manager.clients.models import Client
from house_manager.houses.mixins import GetHouseAndUserMixin
from house_manager.houses.models import House

UserModel = get_user_model()


class ClientCreateView(CheckForLoggedInUserMixin, GetHouseAndUserMixin, views.CreateView):
    queryset = Client.objects.all()
    template_name = "clients/create_client.html"
    form_class = ClientCreateForm

    def form_valid(self, form):
        try:
            return super().form_valid(form)

        except IntegrityError as e:
            error_message = _("Client with this apartment already exist")
            form.add_error(None, error_message)

            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["action_url"] = reverse_lazy("create_client")
        context["title"] = _("Add Client")

        return context

    def get_success_url(self):
        selected_house_id = self.request.session.get("selected_house")

        return reverse_lazy('details_house', kwargs={'pk': selected_house_id})


@method_decorator(get_current_client_id, name='dispatch')
class ClientDetailView(CheckForLoggedInUserMixin, views.DetailView):
    template_name = "clients/details_client.html"

    def get_object(self, queryset=None):
        client = self.request.selected_client
        selected_house_id = self.request.session.get("selected_house")

        if selected_house_id and client.house_id != selected_house_id:
            raise PermissionDenied("Client not found for current house.")
        return client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_house_id = self.request.session.get("selected_house")

        if selected_house_id:
            context["house"] = House.objects.get(pk=selected_house_id)
        else:
            raise Http404("House not found")

        context["clients_bills"] = ClientMonthlyBill.objects.filter(client_id=self.object.id)
        context["client_other_bills"] = ClientOtherBill.objects.filter(client_id=self.object.id)

        return context


@method_decorator(get_current_client_id, name='dispatch')
class ClientEditView(CheckForLoggedInUserMixin, GetHouseAndUserMixin, views.UpdateView):
    template_name = "clients/edit_client.html"
    form_class = ClientEditForm

    # fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied", "is_inhabitable")

    def get_object(self, queryset=None):
        client = self.request.selected_client
        selected_house_id = self.request.session.get("selected_house")

        if selected_house_id and client.house_id != selected_house_id:
            raise PermissionDenied("Client not found for current house.")
        return client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = reverse_lazy("edit_client", kwargs={'pk': self.object.pk})
        context["form_title"] = _("Edit Client")

        return context

    def get_success_url(self):
        return reverse_lazy("house_clients_list", kwargs={"pk": self.object.house.pk})


@method_decorator(get_current_client_id, name='dispatch')
class ClientDeleteView(CheckForLoggedInUserMixin, views.DeleteView):
    template_name = "clients/delete_client.html"

    def get_object(self, queryset=None):
        client = self.request.selected_client
        selected_house_id = self.request.session.get("selected_house")

        if selected_house_id and client.house_id != selected_house_id:
            raise PermissionDenied("Client not found for current house.")
        return client

    def get_success_url(self):
        return reverse_lazy("house_clients_list", kwargs={"pk": self.object.house.pk})
