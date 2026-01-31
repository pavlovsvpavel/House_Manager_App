from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.common.mixins import MonthChoices
from house_manager.houses.decorators import get_current_house_id
from house_manager.houses.forms import HouseCreateForm, HouseCalculationsOptionsEditForm
from house_manager.houses.helpers.house_clients_filter_by_payment_status import house_clients_filter_by_payment_status
from house_manager.houses.models import House, HouseCalculationsOptions


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
class HouseDetailView(CheckForLoggedInUserMixin, views.DetailView):
    template_name = "houses/details_house.html"

    def get_object(self, queryset=None):
        return self.request.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_house_id = self.object.id
        context.update({
            'total_apartments': House.objects.total_apartments(selected_house_id),
            'total_people': House.objects.total_people(selected_house_id),
            'total_people_using_lift': House.objects.total_people_using_lift(selected_house_id),
            'uninhabitable_apartments': House.objects.uninhabitable_apartments(selected_house_id)
        })
        return context


@method_decorator(get_current_house_id, name='dispatch')
class HouseClientsDetailView(CheckForLoggedInUserMixin, views.DetailView):
    template_name = "houses/house_clients_list.html"

    def get_object(self, queryset=None):
        return self.request.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        is_paid = self.request.GET.get('is_paid', None)
        month = self.request.GET.get('month', None)
        clients = self.object.clients.all()

        context["clients"] = house_clients_filter_by_payment_status(clients, is_paid, month)
        context["MonthChoices"] = MonthChoices

        return context


@method_decorator(get_current_house_id, name='dispatch')
class HouseEditView(CheckForLoggedInUserMixin, views.UpdateView):
    template_name = "houses/edit_house.html"
    fields = ("town", "address", "building_number", "entrance", "fixed_monthly_taxes", "money_balance")

    def get_object(self, queryset=None):
        return self.request.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_house = self.get_object()
        user = self.request.user

        calc_options, created = HouseCalculationsOptions.objects.get_or_create(
            house=selected_house,
            user=user,
            defaults={
                'based_on_apartment': [],
                'based_on_total_people': []
            }
        )
        context["calc_options_form"] = HouseCalculationsOptionsEditForm(
            instance=calc_options,
            initial={
                'house': selected_house.id,
                'user': user.id,
            }
        )
        context["form_title"] = _("Edit House")
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.request.user
        form = self.get_form()

        calc_options, created = HouseCalculationsOptions.objects.get_or_create(
            house=self.object,
            user=user,
            defaults={
                'based_on_apartment': [],
                'based_on_total_people': []
            }
        )
        post_data = request.POST.copy()
        post_data.update({
            'house': self.object.id,
            'user': user.id
        })
        calc_options_form = HouseCalculationsOptionsEditForm(
            post_data,
            instance=calc_options
        )

        if form.is_valid() and calc_options_form.is_valid():
            self.object = form.save()
            calc_options_form.save()
            return redirect(self.get_success_url())

        return self.render_to_response(
            self.get_context_data(form=form, calc_form=calc_options_form))

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.pk})


@method_decorator(get_current_house_id, name='dispatch')
class HouseDeleteView(CheckForLoggedInUserMixin, views.DeleteView):
    queryset = House.objects.all()
    template_name = "houses/delete_house.html"

    def get_success_url(self):
        return reverse_lazy('dashboard')
