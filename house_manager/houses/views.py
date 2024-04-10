from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.houses.decorators import get_current_house_id
from house_manager.houses.forms import HouseCreateForm
from house_manager.houses.helpers.house_clients_filter_by_payment_status import filter_by_payment_status
from house_manager.houses.models import House


class HouseCreateView(CheckForLoggedInUserMixin, views.CreateView):
    queryset = House.objects.all()
    template_name = "houses/create_house.html"
    form_class = HouseCreateForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["action_url"] = reverse_lazy("create_house")
        context["title"] = _("Create House")

        return context


@method_decorator(get_current_house_id, name='dispatch')
class HouseDetailView(views.DetailView):
    queryset = House.objects.all()
    template_name = "houses/details_house.html"

    def get(self, request, *args, **kwargs):
        selected_house_id = self.kwargs.get('pk')

        selected_house = House.objects.get(id=selected_house_id)
        request.session['selected_house'] = selected_house.pk

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_house = self.kwargs.get('pk')

        total_apartments = House.objects.total_apartments(selected_house)
        total_people = House.objects.total_people(selected_house)
        total_people_using_lift = House.objects.total_people_using_lift(selected_house)

        context['total_apartments'] = total_apartments
        context['total_people'] = total_people
        context['total_people_using_lift'] = total_people_using_lift

        return context


@method_decorator(get_current_house_id, name='dispatch')
class HouseClientsDetailView(CheckForLoggedInUserMixin, views.DetailView):
    queryset = House.objects.prefetch_related('clients')
    template_name = "houses/house_clients_list.html"

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        is_paid = self.request.GET.get('is_paid', None)
        clients = self.object.clients.all()

        context["clients"] = filter_by_payment_status(clients, is_paid)

        return context


@method_decorator(get_current_house_id, name='dispatch')
class HouseEditView(CheckForLoggedInUserMixin, views.UpdateView):
    queryset = House.objects.all()
    template_name = "houses/edit_house.html"
    fields = ("town", "address", "building_number", "entrance", "money_balance")

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["action_url"] = reverse_lazy("edit_house", kwargs={'pk': self.object.pk})
        context["form_title"] = _("Edit House")

        return context


@method_decorator(get_current_house_id, name='dispatch')
class HouseDeleteView(CheckForLoggedInUserMixin, views.DeleteView):
    queryset = House.objects.all()
    template_name = "houses/delete_house.html"

    def get_success_url(self):
        return reverse_lazy('dashboard')
