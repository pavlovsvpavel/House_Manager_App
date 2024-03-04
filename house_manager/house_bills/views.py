from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.house_bills.models import HouseMonthlyBill
from house_manager.houses.models import House


class HouseMonthlyBillCreateView(views.CreateView):
    queryset = HouseMonthlyBill.objects.all()
    template_name = "house_bills/create_house_bills.html"
    fields = '__all__'

    # fields = ("month", "year", "electricity_common",
    #           "electricity_lift", "internet", "maintenance_lift",
    #           "fee_cleaner", "fee_manager_and_cashier", "repairs",
    #           "others")

    def get_success_url(self):
        return reverse_lazy('list_clients_house', kwargs={'pk': self.object.house.pk})


class HouseMonthlyBillDetailView(views.DetailView):
    queryset = House.objects.all()
    template_name = "house_bills/list_house_bills.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.get_object()

        context['house_bills'] = house.house_monthly_bills.all()

        return context
