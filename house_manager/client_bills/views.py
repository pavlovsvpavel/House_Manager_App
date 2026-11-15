from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
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
from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.clients.mixins import ClientOwnershipMixin
from house_manager.clients.models import Client
from house_manager.common.helpers.filtering_unpaid_client_bills import filtering_unpaid_client_bills
from house_manager.common.mixins import HtmxFragmentMixin, MonthChoices
from house_manager.houses.models import House
from house_manager.house_bills.helpers.filter_bills_by_payment_status import filter_bills_by_payment_status
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

        # Summary line above the list (server-rendered, no JS).
        unpaid = client_bills.filter(is_paid=False)
        context["bills_count"] = client_bills.count()
        context["unpaid_count"] = unpaid.count()
        context["unpaid_total"] = unpaid.aggregate(
            total=Coalesce(Sum("total_amount"), Value(Decimal("0.00"))))["total"]

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

        # Multi-payment: every other unpaid bill of this client, any
        # period - the payment modal lists them as checkboxes and pays
        # them in the same transaction as the bill being opened.
        context['pay_bills'] = (
            self.queryset.model.objects
            .filter(client_id=self.selected_client.pk, is_paid=False)
            .exclude(pk=self.object.pk)
            .order_by("year", "month"))

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

            # Multi-payment: the modal may check other unpaid bills of the
            # same client; they are paid in THIS transaction - one
            # signature on every selected bill, one balance credit.
            pay_ids = [pk for pk in self.request.POST.getlist("pay_bill")
                       if pk.isdigit()]
            self._paid_together_bills = []

            with transaction.atomic():
                # Row locks (#18): the house row and the selected bills are
                # locked before being read, so concurrent payments cannot
                # interleave the balance arithmetic.
                House.objects.select_for_update().get(
                    pk=form.instance.house_id)

                if pay_ids:
                    self._paid_together_bills = list(
                        self.queryset.model.objects.select_for_update()
                        .filter(pk__in=pay_ids,
                                client_id=self.selected_client.pk,
                                house_id=form.instance.house_id,
                                user_id=self.request.user.pk,
                                is_paid=False)
                        .order_by("year", "month"))

                form.save()

                credited = self.queryset.model.objects.filter(
                    pk__in=[form.instance.pk]
                    + [bill.pk for bill in self._paid_together_bills]
                ).aggregate(total=Coalesce(
                    Sum("total_amount"), Value(Decimal("0.00"))))["total"]

                House.objects.filter(pk=form.instance.house_id).update(
                    money_balance=F("money_balance") + credited)

                if self._paid_together_bills:
                    self.queryset.model.objects.filter(
                        pk__in=[bill.pk
                                for bill in self._paid_together_bills]
                    ).update(is_paid=True,
                             signature=form.instance.signature or "")
                    for bill in self._paid_together_bills:
                        bill.is_paid = True
                        bill.signature = form.instance.signature or ""

            if self.is_htmx_request():
                self.object = form.instance
                return self.render_row_fragment()

            return super().form_valid(form)

    def render_row_fragment(self):
        """Return the updated bill rows for an in-place HTMX swap.

        The bill being paid renders as the plain target row; every bill
        paid in the same transaction renders again with hx-swap-oob so
        htmx replaces its row in the list in the same response.
        """
        html = render_to_string(
            self.row_template_name, {"bill": self.object}, request=self.request)
        fragments = [html]
        for bill in getattr(self, "_paid_together_bills", []):
            fragments.append(render_to_string(
                self.row_template_name, {"bill": bill, "oob": True},
                request=self.request))
        response = HttpResponse("\n".join(fragments))
        response["HX-Trigger"] = "billPaid"
        response["X-Paid-Together"] = ",".join(
            str(bill.pk) for bill in getattr(self, "_paid_together_bills", []))
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
    what the payment credited and clears the signature — a payment that
    is undone did not happen. For a multi-payment the toast sends the
    ids of every bill paid in the same transaction and the whole group
    is reverted with one locked balance update.
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

    def post(self, request, *args, **kwargs):
        bill = self.get_object()

        # The undo toast sends the ids of the bills paid in the SAME
        # multi-payment transaction; reverting undoes the whole group.
        # Each id is re-validated for ownership and paid status under a
        # row lock, so stale or forged ids simply do nothing.
        paid_together_ids = [pk for pk in request.POST.getlist("paid_together")
                             if pk.isdigit()]

        reverted_bills = []
        with transaction.atomic():
            if self._bill_paid_before_request:
                reverted_bills.append(bill)

            if paid_together_ids:
                reverted_bills.extend(
                    self.queryset.model.objects.select_for_update()
                    .filter(pk__in=paid_together_ids,
                            client_id=bill.client_id,
                            house_id=bill.house_id,
                            user_id=request.user.pk,
                            is_paid=True)
                    .exclude(pk=bill.pk))

            if reverted_bills:
                # One locked balance update with the group's sum (the
                # inverse of the payment's single credit).
                total_reverted = sum(
                    (b.total_amount for b in reverted_bills),
                    Decimal("0.00"))
                House.objects.select_for_update().get(pk=bill.house_id)
                House.objects.filter(pk=bill.house_id).update(
                    money_balance=F("money_balance") - total_reverted)

                self.queryset.model.objects.filter(
                    pk__in=[b.pk for b in reverted_bills]).update(
                    is_paid=False, signature="")
                for b in reverted_bills:
                    b.is_paid = False
                    b.signature = ""

        if self.is_htmx_request():
            fragments = [render_to_string(
                self.row_template_name, {"bill": bill}, request=request)]
            for extra in reverted_bills:
                if extra.pk == bill.pk:
                    continue
                fragments.append(render_to_string(
                    self.row_template_name,
                    {"bill": extra, "oob": True}, request=request))
            response = HttpResponse("\n".join(fragments))
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
