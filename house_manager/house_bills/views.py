from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.house_bills.forms import HouseMonthlyBillForm
from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.mixins import GetCurrentHouseInstanceMixin
from house_manager.houses.models import House


class HouseMonthlyBillCreateView(GetCurrentHouseInstanceMixin, views.CreateView):
    queryset = HouseMonthlyBill.objects.all()
    template_name = "house_bills/create_house_bills.html"
    form_class = HouseMonthlyBillForm

    object = None

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.house.pk})

    def form_valid(self, form):
        try:
            self.object = form.save()
            current_house_id = self.object.house.pk
            current_year = self.object.year
            current_month = self.object.month
            current_user = self.request.user.pk
            calculate_fees(current_house_id, current_year, current_month, current_user)

            return super().form_valid(form)

        except IntegrityError as e:
            error_message = "House bill with those month and year already exists."
            form.add_error(None, error_message)

            return self.form_invalid(form)


class CurrentHouseMonthlyBillDetailView(views.DetailView):
    # queryset = House.objects.all()
    template_name = "house_bills/list_house_bills.html"

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     house = self.get_object()
    #
    #     context['house_bills'] = house.house_monthly_bills.all()
    #
    #     return context

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["house_bills"] = self.object.house_monthly_bills.all()

        return context


class HouseMonthlyBillDetailView(views.DetailView):
    queryset = HouseMonthlyBill.objects.all()
    template_name = "house_bills/details_house_bills.html"

# TODO: To decide if we need to implement Edit and Delete views
# class HouseMonthlyBillEditView(views.UpdateView):
#     queryset = HouseMonthlyBill.objects.all()
#     template_name = "house_bills/edit_house_bill.html"
#     fields = ("month", "year", "electricity_common",
#               "electricity_lift", "internet", "maintenance_lift",
#               "fee_cleaner", "fee_manager_and_cashier", "repairs",
#               "others")
#
#     def get_success_url(self):
#         return reverse_lazy("list_house_bills", kwargs={"pk": self.object.house.pk})
