from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.house_bills.models import HouseMonthlyBill


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

    # def form_valid(self, form):
    #     # Get the form data
    #     field1 = form.cleaned_data['year']
    #     field2 = form.cleaned_data['month']
    #
    #     # Check if the combination already exists
    #     if HouseMonthlyBill.objects.filter(field1=field1, field2=field2).exists():
    #         form.add_error(None, "Bill with this year and month already exists.")
    #         return self.form_invalid(form)
    #
    #     return super().form_valid(form)
