from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.common.mixins import HtmxFragmentMixin, YearChoices
from house_manager.houses.forms import HouseCreateForm, HouseCalculationsOptionsEditForm
from house_manager.houses.helpers.house_clients_filter_by_payment_status import house_clients_filter_by_payment_status
from house_manager.houses.mixins import HouseOwnershipMixin
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


class HouseDetailView(HouseOwnershipMixin, views.DetailView):
    template_name = "houses/details_house.html"

    def get_object(self, queryset=None):
        return self.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        selected_house_id = self.selected_house.id
        context.update({
            'total_apartments': House.objects.total_apartments(selected_house_id),
            'total_people': House.objects.total_people(selected_house_id),
            'total_people_using_lift': House.objects.total_people_using_lift(selected_house_id),
            'uninhabitable_apartments': House.objects.uninhabitable_apartments(selected_house_id)
        })
        return context


class HouseClientsDetailView(HouseOwnershipMixin, HtmxFragmentMixin, views.DetailView):
    template_name = "houses/house_clients_list.html"
    partial_template_name = "houses/partials/clients_results.html"

    def get_object(self, queryset=None):
        return self.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        is_paid = self.request.GET.get('is_paid', None)
        month = self.request.GET.get('month', None)
        clients = self.selected_house.clients.order_by('floor').all()

        # Floor filter: a typed floor number narrows the list. Anything
        # that is not a plain non-negative integer ("", "abc", "-2")
        # means "no floor filter".
        selected_floor = None
        floor_raw = (self.request.GET.get('floor') or "").strip()
        if floor_raw.isdigit():
            selected_floor = int(floor_raw)
        if selected_floor is not None:
            clients = clients.filter(floor=selected_floor)

        context["selected_floor"] = selected_floor

        # Year filter, same rule as the floor one: only a four-digit value
        # is a real filter; anything else means "no year filter".
        selected_year = None
        year_raw = (self.request.GET.get('year') or "").strip()
        if len(year_raw) == 4 and year_raw.isdigit():
            selected_year = year_raw
        context["selected_year"] = selected_year
        context["YearChoices"] = YearChoices.previous_and_next_years()

        context["clients"] = house_clients_filter_by_payment_status(
            clients, is_paid, month, selected_year)
        if is_paid == 'False':
            context["bills_filter_status"] = 'unpaid'
        elif is_paid == 'True':
            context["bills_filter_status"] = 'paid'
        else:
            context["bills_filter_status"] = 'all'

        return context


class HouseEditView(HouseOwnershipMixin, views.UpdateView):
    template_name = "houses/edit_house.html"
    fields = ("town", "address", "building_number", "entrance", "fixed_monthly_taxes",
              "signature_required", "money_balance")

    def get_object(self, queryset=None):
        return self.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        selected_house = self.selected_house
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
        return reverse_lazy('details_house', kwargs={'house_pk': self.object.pk})


class HouseDeleteView(HouseOwnershipMixin, views.DeleteView):
    template_name = "houses/delete_house.html"

    def get_object(self, queryset=None):
        return self.selected_house

    def get_success_url(self):
        return reverse_lazy('dashboard')
