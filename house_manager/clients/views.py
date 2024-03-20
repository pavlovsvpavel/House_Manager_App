from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404
from django.urls import reverse_lazy
from django.views import generic as views
from django.utils.translation import gettext as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.clients.models import Client
from house_manager.houses.mixins import GetUserAndHouseInstanceMixin
from house_manager.houses.models import House

UserModel = get_user_model()


class ClientCreateView(CheckForLoggedInUserMixin, GetUserAndHouseInstanceMixin, views.CreateView):
    queryset = Client.objects.all()
    template_name = "clients/create_client.html"
    fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get_success_url(self):
        selected_house_pk = self.request.session.get("selected_house")

        return reverse_lazy('details_house', kwargs={'pk': selected_house_pk})

    def form_valid(self, form):
        try:
            return super().form_valid(form)

        except IntegrityError as e:
            error_message = _("Client with this apartment already exist")
            form.add_error(None, error_message)

            return self.form_invalid(form)


class ClientDetailsView(views.DetailView):
    queryset = Client.objects.all().prefetch_related("client_monthly_bills")
    template_name = "clients/details_client.html"

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     house_id = self.request.session.get("selected_house")
    #     if house_id:
    #         context["house"] = House.objects.get(pk=house_id)
    #         context["clients_bills"] = ClientMonthlyBill.objects.filter(client_id=self.object.pk)
    #         context["client_other_bills"] = ClientOtherBill.objects.filter(client_id=self.object.pk)
    #
    #     return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get("selected_house")
        if house_id:
            context["house"] = House.objects.get(pk=house_id)
            client = self.get_object()
            if client.house_id != house_id:
                raise Http404("Client not found in selected house.")
            context["clients_bills"] = ClientMonthlyBill.objects.filter(client_id=client.pk)
            context["client_other_bills"] = ClientOtherBill.objects.filter(client_id=client.pk)
        return context


class ClientEditView(views.UpdateView):
    queryset = Client.objects.prefetch_related("house")
    template_name = "clients/edit_client.html"
    fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied")

    def get_success_url(self):
        return reverse_lazy("list_house_clients", kwargs={"pk": self.object.house.pk})

    def get_object(self, queryset=None):
        client = super().get_object(queryset)
        house_id = self.request.session.get("selected_house")
        if house_id and client.house_id != house_id:
            raise Http404("Client not found in selected house.")
        return client


class ClientDeleteView(views.DeleteView):
    queryset = Client.objects.prefetch_related("house").all()
    template_name = "clients/delete_client.html"

    def get_success_url(self):
        return reverse_lazy("list_house_clients", kwargs={"pk": self.object.house.pk})

    def get_object(self, queryset=None):
        client = super().get_object(queryset)
        house_id = self.request.session.get("selected_house")
        if house_id and client.house_id != house_id:
            raise Http404("Client not found in selected house.")
        return client
