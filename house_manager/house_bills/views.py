from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House


class HouseMonthlyBillCreateView(views.CreateView):
    queryset = HouseMonthlyBill.objects.all()
    template_name = "house_bills/create_house_bills.html"
    # fields = '__all__'

    fields = ("month", "year", "electricity_common",
              "electricity_lift", "internet", "maintenance_lift",
              "fee_cleaner", "fee_manager_and_cashier", "repairs",
              "others")

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.house.pk})

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.get_object()
        context['house'] = house
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)

        form.instance.house = self.get_object()
        form.instance.user = self.request.user

        return form


class HouseMonthlyBillDetailView(views.DetailView):
    queryset = House.objects.all()
    template_name = "house_bills/list_house_bills.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.get_object()

        context['house_bills'] = house.house_monthly_bills.all()

        return context
