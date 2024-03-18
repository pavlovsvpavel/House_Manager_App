from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.client_bills.helpers.add_amount import add_amount_to_house_balance
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.clients.models import Client


class ClientBillsDetailsView(views.DetailView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = "client_bills/list_client_bills.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Client, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["client_bills"] = self.object.client_monthly_bills.all()
        context["client_other_bills"] = self.object.client_other_bills.all()

        return context


class CurrentClientBillEditView(views.UpdateView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = "client_bills/details_client_bill.html"

    fields = ("is_paid",)

    def get_success_url(self):
        return reverse_lazy("list_client_bills", kwargs={"pk": self.object.client.pk})

    def form_valid(self, form):
        if not form.cleaned_data['is_paid']:
            return self.form_invalid(form)
        else:
            house_id = form.instance.house_id
            bill_id = form.instance.id
            type_of_bill = self.queryset.model
            add_amount_to_house_balance(type_of_bill, house_id, bill_id)
            return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form.instance.is_paid:
            form.fields["is_paid"].disabled = True
        return form


class ClientOtherBillsDetailsView(views.DetailView):
    queryset = ClientOtherBill.objects.prefetch_related('client')
    template_name = "client_bills/list_other_client_bills.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Client, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["client_bills"] = self.object.client_other_bills.all()

        return context


class CurrentClientOtherBillEditView(views.UpdateView):
    queryset = ClientOtherBill.objects.prefetch_related('client')
    template_name = "client_bills/details_client_other_bill.html"

    fields = ("is_paid",)

    def get_success_url(self):
        return reverse_lazy("list_other_client_bills", kwargs={"pk": self.object.client.pk})

    def form_valid(self, form):
        if not form.cleaned_data['is_paid']:
            return self.form_invalid(form)
        else:
            house_id = form.instance.house_id
            bill_id = form.instance.id
            type_of_bill = self.queryset.model
            add_amount_to_house_balance(type_of_bill, house_id, bill_id)
            return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form.instance.is_paid:
            form.fields["is_paid"].disabled = True
        return form
