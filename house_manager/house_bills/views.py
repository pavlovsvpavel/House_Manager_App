from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.house_bills.forms import HouseMonthlyBillForm
from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House


class HouseMonthlyBillCreateView(views.CreateView):
    queryset = HouseMonthlyBill.objects.all()
    template_name = "house_bills/create_house_bills.html"
    form_class = HouseMonthlyBillForm

    def get_success_url(self):
        selected_house_pk = self.request.session.get("selected_house")

        return reverse_lazy('details_house', kwargs={'pk': selected_house_pk})

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        house_id = self.request.session.get("selected_house")
        if house_id:
            house = House.objects.get(pk=house_id)
            form.instance.house = house
        form.instance.user = self.request.user

        return form

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
