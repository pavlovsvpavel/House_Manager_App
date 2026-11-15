from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404
from django.urls import reverse_lazy
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.clients.forms import ClientCreateForm, ClientEditForm
from house_manager.clients.mixins import ClientOwnershipMixin
from house_manager.clients.models import Client
from house_manager.houses.mixins import GetHouseAndUserMixin, HouseOwnershipMixin
from house_manager.houses.models import House


class ClientCreateView(CheckForLoggedInUserMixin, HouseOwnershipMixin, GetHouseAndUserMixin, views.CreateView):
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

        context["action_url"] = reverse_lazy(
            "create_client", kwargs={"house_pk": self.selected_house.pk})
        context["title"] = _("Add Client")

        return context

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'house_pk': self.selected_house.pk})


class ClientDetailView(ClientOwnershipMixin, views.DetailView):
    template_name = "clients/details_client.html"

    def get_object(self, queryset=None):
        return self.selected_client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["house"] = self.selected_client.house

        context["clients_bills"] = ClientMonthlyBill.objects.filter(client_id=self.object.id)
        context["client_other_bills"] = ClientOtherBill.objects.filter(client_id=self.object.id)

        return context


class ClientEditView(ClientOwnershipMixin, views.UpdateView):
    template_name = "clients/edit_client.html"
    form_class = ClientEditForm

    def get_object(self, queryset=None):
        return self.selected_client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = reverse_lazy(
            "edit_client", kwargs={"house_pk": self.selected_client.house_id, "pk": self.object.pk})
        context["form_title"] = _("Edit Client")

        return context

    def get_success_url(self):
        return reverse_lazy(
            "house_clients_list", kwargs={"house_pk": self.selected_client.house_id})


class ClientDeleteView(ClientOwnershipMixin, views.DeleteView):
    template_name = "clients/delete_client.html"

    def get_object(self, queryset=None):
        return self.selected_client

    def get_success_url(self):
        return reverse_lazy(
            "house_clients_list", kwargs={"house_pk": self.selected_client.house_id})
