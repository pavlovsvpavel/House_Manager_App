from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.client_bills.helpers.add_amount_to_balance import add_amount_to_house_balance
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.clients.models import Client


class ClientBaseBillsDetailView(CheckForLoggedInUserMixin, views.DetailView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = None

    def get_object(self, queryset=None):
        selected_client_id = self.request.session.get("selected_client")
        if not selected_client_id or selected_client_id != self.kwargs['pk']:
            raise Http404("Client not found for current house.")
        return get_object_or_404(Client, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["client_bills"] = self.get_type_of_client_bills()

        return context

    def get_type_of_client_bills(self):
        raise NotImplementedError("Subclasses must implement get_type_of_client_bills()")


class ClientMonthlyBillsDetailView(ClientBaseBillsDetailView):
    template_name = "client_bills/list_client_bills.html"

    def get_type_of_client_bills(self):
        return self.object.client_monthly_bills.all()


class ClientOtherBillsDetailView(ClientBaseBillsDetailView):
    template_name = "client_bills/list_other_client_bills.html"

    def get_type_of_client_bills(self):
        return self.object.client_other_bills.all()


class CurrentClientBaseBillEditView(CheckForLoggedInUserMixin, views.UpdateView):
    queryset = None
    template_name = None
    success_url_name = None
    fields = ("is_paid",)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name, kwargs={"pk": self.object.client.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get("selected_house")

        current_house = self.object.house.pk
        if current_house != house_id:
            raise Http404(_("Bills not found in selected client."))

        return context

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


class CurrentClientMonthlyBillEditView(CurrentClientBaseBillEditView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = "client_bills/edit_client_bill.html"
    success_url_name = "list_client_bills"


class CurrentClientOtherBillEditView(CurrentClientBaseBillEditView):
    queryset = ClientOtherBill.objects.prefetch_related('client')
    template_name = "client_bills/edit_client_other_bill.html"
    success_url_name = "list_other_client_bills"

