from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from django.views import generic as views
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from weasyprint import HTML
from urllib.parse import quote
from house_manager.client_bills.helpers.add_amount_to_balance import add_amount_to_house_balance
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.clients.mixins import ClientOwnershipMixin
from house_manager.clients.models import Client
from house_manager.common.helpers.filtering_unpaid_client_bills import filtering_unpaid_client_bills
from house_manager.common.mixins import HtmxFragmentMixin, MonthChoices
from house_manager.house_bills.helpers.filter_bills_by_payment_status import filter_bills_by_payment_status
from house_manager.house_bills.helpers.subtract_amount_from_balance import subtract_amount_from_house_balance
from house_manager.houses.mixins import HouseOwnershipMixin


class ClientBaseBillsDetailView(HtmxFragmentMixin, ClientOwnershipMixin, views.DetailView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = None
    partial_template_name = None

    def get_object(self, queryset=None):
        return self.selected_client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        is_paid = self.request.GET.get('is_paid', None)
        month = self.request.GET.get('month', None)
        client_bills = self.get_type_of_client_bills()

        # Same fix as the house lists: filter when either parameter is
        # present, not only when is_paid is in the URL.
        if is_paid is not None or month is not None:
            client_bills = filter_bills_by_payment_status(client_bills, is_paid, month)

        context["client"] = self.selected_client
        context["house"] = self.selected_client.house
        context["client_bills"] = client_bills
        context["MonthChoices"] = MonthChoices

        return context

    def get_type_of_client_bills(self):
        raise NotImplementedError("Subclasses must implement get_type_of_client_bills()")


class ClientMonthlyBillsDetailView(ClientBaseBillsDetailView):
    template_name = "client_bills/list_client_bills.html"
    partial_template_name = "client_bills/partials/monthly_bill_list.html"

    def get_type_of_client_bills(self):
        return self.object.client_monthly_bills.order_by("is_paid", "-year", "-month").all()


class ClientOtherBillsDetailView(ClientBaseBillsDetailView):
    template_name = "client_bills/list_other_client_bills.html"
    partial_template_name = "client_bills/partials/other_bill_list.html"

    def get_type_of_client_bills(self):
        return self.object.client_other_bills.order_by("is_paid", "-year", "-month").all()


class CurrentClientBaseBillEditView(HtmxFragmentMixin, ClientOwnershipMixin, views.UpdateView):
    queryset = None
    template_name = None
    partial_template_name = None
    row_template_name = None
    success_url_name = None
    fields = ("is_paid",)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # The bill must belong to the logged-in user, to the client in the
        # URL and to the house in the URL — the URL is authoritative, no
        # session state is consulted.
        if (obj.user_id != self.request.user.pk
                or obj.client_id != self.kwargs["client_pk"]
                or obj.house_id != self.kwargs["house_pk"]):
            raise Http404(_("Bill not found for current client."))

        # Capture the pristine DB state: binding the form to request.POST
        # mutates the instance, so this must happen before validation.
        self._bill_paid_before_request = obj.is_paid

        return obj

    def get_success_url(self):
        return reverse_lazy(
            self.success_url_name,
            kwargs={
                "house_pk": self.kwargs["house_pk"],
                "client_pk": self.kwargs["client_pk"],
            })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_instance = self.selected_client.house

        unpaid_sum = filtering_unpaid_client_bills(
            client=self.selected_client,
            selected_year=self.object.year,
            selected_month=self.object.month
        )

        context['current_house'] = house_instance
        context['amount_old_debts'] = unpaid_sum

        return context

    def form_valid(self, form):
        # Idempotency guard: a bill that was already paid in the DB must
        # never be re-processed, otherwise replaying the form re-credits the
        # house balance. NOTE: form.instance.is_paid already reflects the
        # submitted POST data, so the pristine value captured in get_object()
        # is used instead.
        if getattr(self, "_bill_paid_before_request", False):
            return self.form_invalid(form)

        if not form.cleaned_data['is_paid']:
            return self.form_invalid(form)

        else:
            signature_data = self.request.POST.get('signature')
            if signature_data:
                signature_base64 = f"data:image/svg+xml;base64,{signature_data}"
                form.instance.signature = signature_base64

            house_id = form.instance.house_id
            bill_id = form.instance.id
            type_of_bill = self.queryset.model
            add_amount_to_house_balance(type_of_bill, house_id, bill_id)

            if self.is_htmx_request():
                self.object = form.save()
                return self.render_row_fragment()

            return super().form_valid(form)

    def render_row_fragment(self):
        """Return just the updated bill row for an in-place HTMX swap."""
        html = render_to_string(
            self.row_template_name, {"bill": self.object}, request=self.request)
        response = HttpResponse(html)
        response["HX-Trigger"] = "billPaid"
        return response

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form.instance.is_paid:
            form.fields["is_paid"].disabled = True
        return form

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.is_htmx_request():
            # Keep validation errors inside the open payment dialog instead
            # of replacing the bill row with a modal fragment.
            response["HX-Retarget"] = "#bill-modal-container"
            response["HX-Reswap"] = "innerHTML"
        return response


class CurrentClientMonthlyBillEditView(CurrentClientBaseBillEditView):
    queryset = ClientMonthlyBill.objects.prefetch_related('client')
    template_name = "client_bills/edit_client_bill.html"
    partial_template_name = "client_bills/partials/monthly_bill_modal.html"
    row_template_name = "client_bills/partials/monthly_bill_row.html"
    success_url_name = "list_client_bills"


class CurrentClientOtherBillEditView(CurrentClientBaseBillEditView):
    queryset = ClientOtherBill.objects.prefetch_related('client')
    template_name = "client_bills/edit_client_other_bill.html"
    partial_template_name = "client_bills/partials/other_bill_modal.html"
    row_template_name = "client_bills/partials/other_bill_row.html"
    success_url_name = "list_other_client_bills"


class ClientBaseBillRevertView(ClientOwnershipMixin, HtmxFragmentMixin, views.View):
    """Undo a client bill payment (the Phase 3 toast's "Undo" button).

    Owner-only, POST-only, and idempotent. The revert subtracts exactly
    what the payment credited (total_amount) and clears the signature —
    a payment that is undone did not happen.
    """
    queryset = None
    row_template_name = None
    success_url_name = None

    def get_object(self):
        bill = get_object_or_404(self.queryset, pk=self.kwargs["pk"])

        # The bill must belong to the logged-in user, to the client in the
        # URL and to the house in the URL — same rule as the edit views.
        if (bill.user_id != self.request.user.pk
                or bill.client_id != self.kwargs["client_pk"]
                or bill.house_id != self.kwargs["house_pk"]):
            raise Http404(_("Bill not found for current client."))

        self._bill_paid_before_request = bill.is_paid
        return bill

    def revert(self, bill):
        if self._bill_paid_before_request:
            # subtract_amount_from_house_balance special-cases HouseMonthlyBill
            # by class name; for client bills it subtracts total_amount, which
            # is exactly the inverse of add_amount_to_house_balance.
            subtract_amount_from_house_balance(self.queryset.model, bill.house_id, bill.pk)
            bill.is_paid = False
            bill.signature = ""
            bill.save(update_fields=["is_paid", "signature"])

    def post(self, request, *args, **kwargs):
        bill = self.get_object()
        self.revert(bill)

        if self.is_htmx_request():
            html = render_to_string(
                self.row_template_name, {"bill": bill}, request=request)
            response = HttpResponse(html)
            response["HX-Trigger"] = "billReverted"
            return response

        return redirect(reverse(
            self.success_url_name,
            kwargs={
                "house_pk": self.kwargs["house_pk"],
                "client_pk": self.kwargs["client_pk"],
            }))


class CurrentClientMonthlyBillRevertView(ClientBaseBillRevertView):
    queryset = ClientMonthlyBill.objects
    row_template_name = "client_bills/partials/monthly_bill_row.html"
    success_url_name = "list_client_bills"


class CurrentClientOtherBillRevertView(ClientBaseBillRevertView):
    queryset = ClientOtherBill.objects
    row_template_name = "client_bills/partials/other_bill_row.html"
    success_url_name = "list_other_client_bills"


class DownloadReceiptView(HouseOwnershipMixin, DetailView):
    template_name = 'partials/receipt_pdf.html'
    context_object_name = 'bill'

    def get_queryset(self):
        # Only the bill's owner may download its receipt (prevents IDOR),
        # and only within the house from the URL.
        return ClientMonthlyBill.objects.filter(
            user=self.request.user,
            house_id=self.kwargs["house_pk"],
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        bill = self.object

        if not bill.is_paid:
            return HttpResponse("Receipt is not available for unpaid bills.", status=400)

        context = self.get_context_data(object=self.object)
        html_string = render_to_string(self.template_name, context, request=request)

        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')

        raw_filename = f"receipt-{bill.client.family_name}-{bill.get_month_name()}-{bill.year}"

        clean_filename = f"{slugify(raw_filename, allow_unicode=True)}.pdf"

        encoded_filename = quote(clean_filename)

        response['Content-Disposition'] = f"attachment; filename*=utf-8''{encoded_filename}"

        return response
