from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views


from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client


class ClientBillsDetailsView(views.DetailView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = "client_bills/list_client_bills.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Client, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["client_bills"] = self.object.client_monthly_bills.all()

        return context


class CurrentClientBillEditView(views.UpdateView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = "client_bills/details_client_bill.html"

    fields = ("is_paid",)

    def get_success_url(self):
        return reverse_lazy("list_client_bills", kwargs={"pk": self.object.client.pk})
