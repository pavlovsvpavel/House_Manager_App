from django.contrib.auth import get_user_model
from django.db import IntegrityError

from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client
from house_manager.common.mixins import MonthChoices
from house_manager.house_bills.helpers.choices_for_year_field import next_five_years
from house_manager.houses.mixins import GetCurrentHouseInstanceMixin
from house_manager.houses.models import House

UserModel = get_user_model()


class ClientCreateView(GetCurrentHouseInstanceMixin, views.CreateView):
    queryset = Client.objects.all()
    template_name = "clients/create_client.html"
    fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied", "fixed_fee")

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.house.pk})

    # def get_object(self, queryset=None):
    #     return get_object_or_404(House, pk=self.kwargs["pk"])
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     house_id = self.request.session.get("selected_house_id")
    #     if house_id:
    #         context["house"] = House.objects.get(pk=house_id)
    #     return context
    #
    # def get_form(self, form_class=None):
    #     form = super().get_form(form_class=form_class)
    #     house_id = self.request.session.get("selected_house_id")
    #     if house_id:
    #         house = House.objects.get(pk=house_id)
    #         form.instance.house = house
    #     form.instance.user = self.request.user
    #
    #     return form

    def form_valid(self, form):
        try:
            return super().form_valid(form)

        except IntegrityError as e:
            error_message = "Client with this apartment is already exist"
            form.add_error(None, error_message)

            return self.form_invalid(form)


class ClientDetailsView(views.DetailView):
    queryset = Client.objects.all().prefetch_related("client_monthly_bills")
    template_name = "clients/details_client.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get("selected_house_id")
        if house_id:
            context["house"] = House.objects.get(pk=house_id)
            context["clients_bills"] = ClientMonthlyBill.objects.filter(client_id=self.object.pk)

        return context

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     queryset = self.filter_by_period(queryset)
    #
    #     return queryset
    #
    # def filter_by_period(self, queryset):
    #     search_year = self.request.GET.get('search_year', None)
    #     search_month = self.request.GET.get('search_month', None)
    #     # client = self.get_object()
    #
    #     filter_query = {
    #         "id": self.object.pk,
    #     }
    #
    #     if search_year and search_month:
    #         filter_query["client_monthly_bills__year"] = search_year
    #         filter_query["client_monthly_bills__month"] = search_month
    #
    #     result = queryset.filter(**filter_query)
    #
    #     return result


class ClientEditView(views.UpdateView):
    queryset = Client.objects.prefetch_related("house")
    template_name = "clients/edit_client.html"
    fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied", "fixed_fee")

    def get_success_url(self):
        return reverse_lazy("list_house_clients", kwargs={"pk": self.object.house.pk})


class ClientDeleteView(views.DeleteView):
    queryset = Client.objects.prefetch_related("house").all()
    template_name = "clients/delete_client.html"

    def get_success_url(self):
        return reverse_lazy("list_house_clients", kwargs={"pk": self.object.house.pk})
