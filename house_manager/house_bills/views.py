import logging
from decimal import Decimal
from types import SimpleNamespace

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.client_bills.helpers.calculate_fees_other_bills import calculate_fees_other_bills
from house_manager.client_bills.helpers.calculate_fixed_bills import calculate_fixed_client_bills
from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client
from house_manager.common.helpers.bills_summary import bills_summary, filtered_bills
from house_manager.common.mixins import HtmxFragmentMixin, MonthChoices, YearChoices
from house_manager.house_bills.forms import HouseMonthlyBillForm, HouseOtherBillForm, HouseFixedBillForm
from house_manager.house_bills.helpers.filter_bills_by_payment_status import filter_bills_by_payment_status
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill, TypeOfBillChoices
from house_manager.houses.mixins import GetHouseAndUserMixin, HouseOwnershipMixin
from house_manager.houses.models import House, HouseCalculationsOptions

logger = logging.getLogger(__name__)


def house_bill_balance_delta(bill):
    """The amount a house bill moves the house balance by: monthly bills
    debit amount_without_repairs (the repairs fund is tracked
    separately), every other bill its total."""
    if isinstance(bill, HouseMonthlyBill):
        return bill.amount_without_repairs()
    return bill.total_amount


class HouseBaseBillCreateView(CheckForLoggedInUserMixin, HouseOwnershipMixin, GetHouseAndUserMixin, views.CreateView):
    template_name = None
    form_class = None
    action_url_name = None
    title = None

    @property
    def current_house(self):
        # Ownership-verified house derived from the URL (house_pk).
        return self.selected_house

    def get_action_url(self):
        # The create routes are nested under /houses/<house_pk>/..., so the
        # form target must be reversed per-request with the house from the URL.
        return reverse(
            self.action_url_name, kwargs={"house_pk": self.selected_house.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.current_house
        context['house'] = house

        if house:
            context['clients'] = Client.objects.filter(house=house)

        context['action_url'] = self.get_action_url()
        context["title"] = self.title
        return context

    def get_success_url(self):
        return reverse_lazy(
            'details_house', kwargs={'house_pk': self.selected_house.pk})


class HouseMonthlyBillCreateView(HouseBaseBillCreateView):
    template_name = "house_bills/create_house_bills.html"
    form_class = HouseMonthlyBillForm
    action_url_name = "create_house_bills"
    title = _("Add monthly bill")

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object: HouseMonthlyBill = form.save()

                if not self.object.house.fixed_monthly_taxes:
                    calculate_fees(
                        form.instance.house.id,
                        form.instance.year,
                        form.instance.month,
                        form.instance.user.pk
                    )
                messages.success(self.request, _("Monthly bill created successfully."))
                return redirect(self.get_success_url())

        except IntegrityError:
            form.add_error(None, _("Bill with those month and year already exists."))
            return self.form_invalid(form)

        except HouseCalculationsOptions.DoesNotExist:
            form.add_error(None, _("Calculation settings are missing."))
            return self.form_invalid(form)


class HouseOtherBillCreateView(HouseBaseBillCreateView):
    template_name = "house_bills/create_other_bill.html"
    form_class = HouseOtherBillForm
    action_url_name = "create_other_bill"
    title = _("Add other bill")

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object: HouseOtherBill = form.save()

                if self.object.type_of_bill != "Single bill":
                    calculate_fees_other_bills(
                        self.object.house.id,
                        self.object.year,
                        self.object.month,
                        self.object.user.pk,
                        self.object.pk
                    )

                messages.success(self.request, _("Other bill created successfully."))
                return redirect(self.get_success_url())

        except IntegrityError:
            form.add_error(None, _("Bill with those month and year already exists."))
            return self.form_invalid(form)


class HouseFixedMonthlyBillView(HouseBaseBillCreateView):
    template_name = "house_bills/create_house_bills.html"
    form_class = HouseFixedBillForm
    action_url_name = "create_fixed_bill"
    title = _("Add Monthly Bill (Per Apartment)")

    def form_valid(self, form):
        house = form.instance.house
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']
        fixed_amount = form.cleaned_data['fixed_amount']
        user_id = form.instance.user.pk

        if ClientMonthlyBill.objects.filter(house=house, year=year, month=month).exists():
            form.add_error(None, _("Client bills for this month and year already exist."))
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                created_count = calculate_fixed_client_bills(
                    house_id=house.id,
                    year=year,
                    month=month,
                    fixed_amount=fixed_amount,
                    user_id=user_id
                )

                msg = _("Successfully created bills for %(count)d apartments.") % {'count': created_count}
                messages.success(self.request, msg)
                return redirect(self.get_success_url())

        except Exception:
            logger.exception("Fixed monthly bill creation failed for house %s", house.id)
            form.add_error(None, _("An error occurred while creating the bills. Please try again."))
            return self.form_invalid(form)


class CurrentHouseBaseBillDetailView(HtmxFragmentMixin, HouseOwnershipMixin, views.DetailView):
    template_name = None
    partial_template_name = None

    def get_object(self, queryset=None):
        return self.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_house = self.selected_house

        is_paid = self.request.GET.get('is_paid', None)
        month = self.request.GET.get('month', None)
        year = self.request.GET.get('year', None)

        house_bills = self.get_type_of_house_bills()

        # The chips always submit all three groups (radios with an "All"
        # chip each); the helper no-ops on "" / None, so calling it
        # unconditionally keeps every combination working.
        house_bills = filter_bills_by_payment_status(house_bills, is_paid, month, year)

        # Summary line above the list (server-rendered, no JS).
        context.update(bills_summary(house_bills))

        context["house"] = current_house
        context["house_bills"] = house_bills
        context["MonthChoices"] = MonthChoices
        context["YearChoices"] = YearChoices.previous_and_next_years()

        return context

    def get_type_of_house_bills(self):
        raise NotImplementedError("Subclasses must implement get_type_of_house_bills()")


class CurrentHouseMonthlyBillDetailView(CurrentHouseBaseBillDetailView):
    template_name = "house_bills/list_house_bills.html"
    partial_template_name = "house_bills/partials/monthly_bill_list.html"

    def get_type_of_house_bills(self):
        return self.object.house_monthly_bills.order_by("is_paid", "-year", "-month").all()


class CurrentHouseOtherBillDetailView(CurrentHouseBaseBillDetailView):
    template_name = "house_bills/list_other_house_bills.html"
    partial_template_name = "house_bills/partials/other_bill_list.html"

    def get_type_of_house_bills(self):
        return self.object.house_other_bills.order_by("is_paid", "-year", "-month").all()


class HouseBaseBillEditView(HtmxFragmentMixin, HouseOwnershipMixin, views.UpdateView):
    queryset = None
    template_name = None
    partial_template_name = None
    row_template_name = None
    success_url_name = None
    fields = ("is_paid",)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # The bill must belong to the logged-in user and to the house in the
        # URL — the URL is authoritative, no session state is consulted.
        if obj.user_id != self.request.user.pk or obj.house_id != self.kwargs["house_pk"]:
            raise Http404(_("Bill not found for current user."))

        # Capture the pristine DB state: binding the form to request.POST
        # mutates the instance, so this must happen before validation.
        self._bill_paid_before_request = obj.is_paid

        return obj

    def form_valid(self, form):
        # Idempotency guard: a bill that was already paid in the DB must
        # never be re-processed, otherwise replaying the form re-credits or
        # re-debits the house balance. NOTE: form.instance.is_paid already
        # reflects the submitted POST data, so the pristine value captured
        # in get_object() is used instead.
        if getattr(self, "_bill_paid_before_request", False):
            return self.form_invalid(form)

        if not form.cleaned_data['is_paid']:
            return self.form_invalid(form)
        else:
            with transaction.atomic():
                # Row locks (#18): the house row is locked before anything
                # reads or writes, and the bill is re-checked under that
                # lock - two concurrent payments cannot both pass the
                # unpaid check and debit the balance twice. (Same pattern
                # as the client-bill flows.)
                House.objects.select_for_update().get(
                    pk=form.instance.house_id)

                still_unpaid = (
                    self.queryset.model.objects.select_for_update()
                    .filter(pk=form.instance.pk, is_paid=False).exists())
                if not still_unpaid:
                    return self.form_invalid(form)

                delta = house_bill_balance_delta(form.instance)

                if self.is_htmx_request():
                    self.object = form.save()
                    response = self.render_row_fragment()
                else:
                    response = super().form_valid(form)

                House.objects.filter(pk=form.instance.house_id).update(
                    money_balance=F("money_balance") - delta)

            return response

    def render_row_fragment(self):
        """Return the updated bill row plus a fresh summary line for an
        in-place HTMX swap.

        ``HX-Trigger: billPaid`` lets the client close the payment dialog and
        restore focus without a full page reload; the summary swaps
        out-of-band so the "Unpaid / Due" numbers track the payment.
        """
        html = render_to_string(
            self.row_template_name, {"bill": self.object}, request=self.request)
        summary_bills = filtered_bills(
            self.queryset.model.objects.filter(
                house_id=self.selected_house.pk),
            self.request)
        summary = render_to_string(
            "partials/bills_summary.html",
            dict(bills_summary(summary_bills), oob=True),
            request=self.request)
        response = HttpResponse("\n".join([html, summary]))
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

    def get_success_url(self):
        return reverse_lazy(
            self.success_url_name,
            kwargs={"house_pk": self.selected_house.pk},
        )


class HouseMonthlyBillEditView(HouseBaseBillEditView):
    queryset = HouseMonthlyBill.objects.prefetch_related("house")
    template_name = "house_bills/edit_house_bills.html"
    partial_template_name = "house_bills/partials/monthly_bill_modal.html"
    row_template_name = "house_bills/partials/monthly_bill_row.html"
    success_url_name = "list_house_bills"


class HouseOtherBillEditView(HouseBaseBillEditView):
    queryset = HouseOtherBill.objects.prefetch_related("house")
    template_name = "house_bills/edit_other_house_bills.html"
    partial_template_name = "house_bills/partials/other_bill_modal.html"
    row_template_name = "house_bills/partials/other_bill_row.html"
    success_url_name = "list_other_house_bills"


class HouseBaseBillRevertView(HouseOwnershipMixin, HtmxFragmentMixin, views.View):
    """Undo a payment (the Phase 3 toast's "Undo" button).

    Owner-only, POST-only, and idempotent: the balance delta paid is
    restored exactly (amount_without_repairs for monthly bills), the bill
    goes back to unpaid, and reverting an already-unpaid bill only
    re-renders the row without touching the balance.
    """
    queryset = None
    row_template_name = None
    success_url_name = None

    def get_object(self):
        bill = get_object_or_404(self.queryset, pk=self.kwargs["pk"])

        # The bill must belong to the logged-in user and to the house in
        # the URL — same rule as the edit views.
        if bill.user_id != self.request.user.pk or bill.house_id != self.kwargs["house_pk"]:
            raise Http404(_("Bill not found for current user."))

        # Pristine DB state, captured before any mutation (same pattern as
        # the payment idempotency guard).
        self._bill_paid_before_request = bill.is_paid
        return bill

    def revert(self, bill):
        with transaction.atomic():
            # Row locks (#18): the house row is locked before the balance
            # update, and the bill is re-checked under that lock - two
            # concurrent reverts cannot both credit the balance.
            House.objects.select_for_update().get(pk=bill.house_id)

            still_paid = (
                self.queryset.model.objects.select_for_update()
                .filter(pk=bill.pk, is_paid=True).exists())
            if not still_paid:
                return

            amount = house_bill_balance_delta(bill)
            House.objects.filter(pk=bill.house_id).update(
                money_balance=F("money_balance") + amount)

            bill.is_paid = False
            bill.save(update_fields=["is_paid"])

    def post(self, request, *args, **kwargs):
        bill = self.get_object()
        self.revert(bill)

        if self.is_htmx_request():
            html = render_to_string(
                self.row_template_name, {"bill": bill}, request=request)
            # Fresh summary line after the undo, same as the payment
            # response does.
            summary_bills = filtered_bills(
                self.queryset.model.objects.filter(house_id=bill.house_id),
                request)
            summary = render_to_string(
                "partials/bills_summary.html",
                dict(bills_summary(summary_bills), oob=True),
                request=request)
            response = HttpResponse("\n".join([html, summary]))
            response["HX-Trigger"] = "billReverted"
            return response

        # No undo UI exists without JS; a crafted POST just goes back to
        # the list.
        return redirect(
            reverse(self.success_url_name, kwargs={"house_pk": self.selected_house.pk}))


class HouseMonthlyBillRevertView(HouseBaseBillRevertView):
    queryset = HouseMonthlyBill.objects
    row_template_name = "house_bills/partials/monthly_bill_row.html"
    success_url_name = "list_house_bills"


class HouseOtherBillRevertView(HouseBaseBillRevertView):
    queryset = HouseOtherBill.objects
    row_template_name = "house_bills/partials/other_bill_row.html"
    success_url_name = "list_other_house_bills"


class ReportMonthlyBillView(HouseOwnershipMixin, views.DetailView):
    template_name = "common/reports_bills.html"

    def get_object(self, queryset=None):
        return self.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_house = self.object

        # The month select is <select multiple>: it posts the month once
        # per selection. An empty list (nothing selected) matches no bills.
        selected_months = [month for month in self.request.GET.getlist("month") if month]
        selected_year = self.request.GET.get("year")

        context["MonthChoices"] = MonthChoices
        context["YearChoices"] = YearChoices.previous_and_next_years()

        context["current_house"] = current_house

        # Re-render the search form with the picked search preserved.
        context["selected_months"] = selected_months
        context["selected_year"] = selected_year

        # The details card lists the selected months as numbers ("01, 02, 03").
        context["selected_months_display"] = ", ".join(selected_months)
        # A signature cannot be summed across months, so multi-month reports
        # swap the Signature column for Paid ("Yes" when every selected
        # month's bill for the client is paid).
        context["is_multi_month"] = len(selected_months) > 1

        # One query for the whole table: select_related joins the client that
        # the row templates read on every row (family_name/apartment) and the
        # multi-month grouping reads per bill. The first row doubles as
        # context["bill"], whose year is all the details card displays
        # (list() keeps the model ordering, so [0] is the old .first()).
        month_bills = list(current_house.client_house_monthly_bills
                           .filter(month__in=selected_months, year=selected_year)
                           .select_related("client"))

        context["bill"] = month_bills[0] if month_bills else None

        if context["is_multi_month"]:
            clients_bills = summarize_bills_per_client(month_bills)
        else:
            clients_bills = month_bills

        context["clients_bills"] = clients_bills

        clients_bills_total_amount = (
            current_house.client_house_monthly_bills
            .filter(month__in=selected_months, year=selected_year)
            .aggregate(total_amount=Coalesce(Sum("total_amount"), Value(Decimal("0.00"))))["total_amount"]
        )

        context["clients_bills_total_amount"] = clients_bills_total_amount

        unpaid_bills = (
            current_house.client_house_monthly_bills
            .filter(month__in=selected_months, year=selected_year)
            .aggregate(amount_old_debts=Coalesce(Sum("amount_old_debts"), Value(Decimal("0.00"))))["amount_old_debts"]
        )

        context["unpaid_bills"] = unpaid_bills

        # Calculate total amount of current month bills and unpaid bills from previous months
        context["amount_for_collection"] = clients_bills_total_amount + unpaid_bills

        return context


class ReportOtherBillView(HouseOwnershipMixin, views.DetailView):
    template_name = "common/reports_other_bills.html"

    def get_object(self, queryset=None):
        return self.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_house = self.selected_house

        # <select multiple> posts the month once per selection.
        selected_months = [month for month in self.request.GET.getlist("month") if month]
        selected_year = self.request.GET.get("year")
        selected_type_of_bill = self.request.GET.get("type_of_bill")

        context["MonthChoices"] = MonthChoices
        context["YearChoices"] = YearChoices.previous_and_next_years()
        context["TypeOfBillChoices"] = TypeOfBillChoices

        context["current_house"] = current_house

        # Re-render the search form with the picked search preserved.
        context["selected_months"] = selected_months
        context["selected_year"] = selected_year
        context["selected_type_of_bill"] = selected_type_of_bill

        # The details card lists the selected months as numbers ("01, 02, 03").
        context["selected_months_display"] = ", ".join(selected_months)
        # A signature cannot be summed across months: multi-month reports
        # swap the Signature column for Paid (all selected months paid).
        context["is_multi_month"] = len(selected_months) > 1

        if selected_type_of_bill == "Bill for all clients":
            # select_related joins the client the row templates read on every
            # row (and the multi-month grouping reads per bill) — one query
            # for the whole table instead of one per row.
            clients_bills = (current_house.client_house_other_bills
                             .filter(month__in=selected_months, year=selected_year)
                             .select_related("client"))

            if context["is_multi_month"]:
                clients_bills = summarize_bills_per_client(clients_bills)

            context["clients_bills"] = clients_bills

            clients_bills_total_amount = (
                current_house.client_house_other_bills
                .filter(month__in=selected_months, year=selected_year)
                .aggregate(total_amount=Coalesce(Sum("total_amount"), Value(Decimal("0.00"))))["total_amount"]
            )

            context["clients_bills_total_amount"] = clients_bills_total_amount

            context["bill"] = (
                current_house.house_other_bills
                .filter(month__in=selected_months, year=selected_year, type_of_bill=selected_type_of_bill)
                .first()
            )
        else:
            context.pop("clients_bills", None)

            single_bills = (
                current_house.house_other_bills
                .filter(month__in=selected_months,
                        year=selected_year,
                        type_of_bill=selected_type_of_bill)
            )

            calculated_total_amount = single_bills.aggregate(
                total_amount=Sum("total_amount"))["total_amount"]

            context["single_bills"] = single_bills
            context["calculated_total_amount"] = calculated_total_amount

        return context


def summarize_bills_per_client(bills):
    """Multi-month reports collapse one-bill-per-month rows into one row
    per client with the money columns summed over the selected months.

    Returns plain row objects carrying the attributes the report templates
    read (client, amount_old_debts, total_amount, is_paid, signature): a
    signature cannot be summed, so multi-month rows have none and the
    templates show the Paid column instead.
    """
    grouped = {}
    for bill in bills:
        row = grouped.setdefault(bill.client_id, {
            "client": bill.client,
            "amount_old_debts": Decimal("0.00"),
            "total_amount": Decimal("0.00"),
            "paid_all": True,
        })
        row["amount_old_debts"] += getattr(bill, "amount_old_debts", None) or Decimal("0.00")
        row["total_amount"] += bill.total_amount or Decimal("0.00")
        row["paid_all"] = row["paid_all"] and bill.is_paid

    return [
        SimpleNamespace(
            client=row["client"],
            amount_old_debts=row["amount_old_debts"],
            total_amount=row["total_amount"],
            is_paid=row["paid_all"],
            signature=None,
        )
        for row in grouped.values()
    ]
