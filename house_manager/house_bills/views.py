from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.clients.models import Client
from house_manager.house_bills.forms import HouseMonthlyBillForm
from house_manager.house_bills.helpers.subtract_amount import subtract_amount_from_house_balance
from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.mixins import GetUserAndHouseInstanceMixin
from house_manager.houses.models import House


class HouseMonthlyBillCreateView(GetUserAndHouseInstanceMixin, views.CreateView):
    queryset = HouseMonthlyBill.objects.select_related('house')
    template_name = "house_bills/create_house_bills.html"
    form_class = HouseMonthlyBillForm

    def get_success_url(self):
        selected_house_pk = self.request.session.get("selected_house")

        return reverse_lazy('details_house', kwargs={'pk': selected_house_pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get("selected_house")

        context['house_id'] = house_id
        context['clients'] = Client.objects.filter(house=house_id)

        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            current_year = form.instance.year
            current_month = form.instance.month
            house_id = form.instance.house_id
            user_id = self.request.user.pk
            calculate_fees(house_id, current_year, current_month, user_id)

            return response

        except IntegrityError as e:
            error_message = "House bill with those month and year already exists."
            form.add_error(None, error_message)

            return self.form_invalid(form)


class CurrentHouseMonthlyBillDetailView(views.DetailView):
    template_name = "house_bills/list_house_bills.html"

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["house_bills"] = self.object.house_monthly_bills.all()

        return context


# class HouseMonthlyBillDetailView(views.DetailView):
#     queryset = HouseMonthlyBill.objects.select_related("house")
#     template_name = "house_bills/details_house_bills.html"


class HouseMonthlyBillEditView(views.UpdateView):
    queryset = HouseMonthlyBill.objects.prefetch_related("house")
    template_name = "house_bills/details_house_bills.html"

    fields = ("is_paid",)

    def get_success_url(self):
        return reverse_lazy("list_house_bills", kwargs={"pk": self.object.house.pk})

    def form_valid(self, form):
        if not form.cleaned_data['is_paid']:
            return self.form_invalid(form)
        else:
            house_id = form.instance.house_id
            bill_id = form.instance.id
            subtract_amount_from_house_balance(house_id, bill_id)
            return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form.instance.is_paid:
            form.fields["is_paid"].disabled = True
        return form


