from decimal import Decimal
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.db.models import Sum, Value
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
from house_manager.common.mixins import HtmxFragmentMixin, MonthChoices, YearChoices
from house_manager.house_bills.forms import HouseMonthlyBillForm, HouseOtherBillForm, HouseFixedBillForm
from house_manager.house_bills.helpers.filter_bills_by_payment_status import filter_bills_by_payment_status
from house_manager.house_bills.helpers.restore_balance_on_revert import restore_house_balance_on_revert
from house_manager.house_bills.helpers.subtract_amount_from_balance import subtract_amount_from_house_balance
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill, TypeOfBillChoices
from house_manager.houses.mixins import GetHouseAndUserMixin, HouseOwnershipMixin
from house_manager.houses.models import House, HouseCalculationsOptions


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

    def render_success_alert(self, form, message):
        """
        Renders the page with a Success Popup.
        """
        context = self.get_context_data(form=form)
        context['sweet_alert'] = {
            'title': _("Success!"),
            'text': message,
            'icon': 'success',
            'redirect_url': self.get_success_url()
        }
        return self.render_to_response(context)

    def form_invalid(self, form):
        """
        Automatically extracts the first error found in the form
        and renders the Error Popup.
        """
        context = self.get_context_data(form=form)
        error_message = _("Please correct the errors below.")

        if form.non_field_errors():
            error_message = form.non_field_errors()[0]
        elif form.errors:
            first_field = next(iter(form.errors))
            error_message = f"{first_field}: {form.errors[first_field][0]}"

        context['sweet_alert'] = {
            'title': _("Error"),
            'text': error_message,
            'icon': 'error',
            'redirect_url': None
        }
        return self.render_to_response(context)


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
                return self.render_success_alert(form, _("Successfully created bill."))

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

                return self.render_success_alert(form, _("Successfully created bill."))

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
                return self.render_success_alert(form, msg)

        except Exception as e:
            form.add_error(None, _("An error occurred: ") + str(e))
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

        house_bills = self.get_type_of_house_bills()

        # Filter when either parameter is present: the month select submits
        # only "month", the debt links submit "is_paid" (with an empty month
        # when "All" is selected). Previously filtering ran only when
        # is_paid was present, so a month choice alone showed every month.
        if is_paid is not None or month is not None:
            house_bills = filter_bills_by_payment_status(house_bills, is_paid, month)

        context["house"] = current_house
        context["house_bills"] = house_bills
        context["MonthChoices"] = MonthChoices

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
            house_id = form.instance.house_id
            bill_id = form.instance.id
            type_of_bill = self.queryset.model
            subtract_amount_from_house_balance(type_of_bill, house_id, bill_id)

            if self.is_htmx_request():
                self.object = form.save()
                return self.render_row_fragment()

            return super().form_valid(form)

    def render_row_fragment(self):
        """Return just the updated bill row for an in-place HTMX swap.

        ``HX-Trigger: billPaid`` lets the client close the payment dialog and
        restore focus without a full page reload.
        """
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
        if self._bill_paid_before_request:
            restore_house_balance_on_revert(self.queryset.model, bill.house_id, bill.pk)
            bill.is_paid = False
            bill.save(update_fields=["is_paid"])

    def post(self, request, *args, **kwargs):
        bill = self.get_object()
        self.revert(bill)

        if self.is_htmx_request():
            html = render_to_string(
                self.row_template_name, {"bill": bill}, request=request)
            response = HttpResponse(html)
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

        selected_month = self.request.GET.get("month")
        selected_year = self.request.GET.get("year")

        context["MonthChoices"] = MonthChoices
        context["YearChoices"] = YearChoices.previous_and_next_years()

        context["current_house"] = current_house

        context["bill"] = (current_house.client_house_monthly_bills
                           .filter(month=selected_month, year=selected_year).first())

        clients_bills = (current_house.client_house_monthly_bills
                         .filter(month=selected_month, year=selected_year))

        context["clients_bills"] = clients_bills

        clients_bills_total_amount = (
            current_house.client_house_monthly_bills
            .filter(month=selected_month, year=selected_year)
            .aggregate(total_amount=Coalesce(Sum("total_amount"), Value(Decimal("0.00"))))["total_amount"]
        )

        context["clients_bills_total_amount"] = clients_bills_total_amount

        unpaid_bills = (
            current_house.client_house_monthly_bills
            .filter(month=selected_month, year=selected_year)
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

        selected_month = self.request.GET.get("month")
        selected_year = self.request.GET.get("year")
        selected_type_of_bill = self.request.GET.get("type_of_bill")

        context["MonthChoices"] = MonthChoices
        context["YearChoices"] = YearChoices.previous_and_next_years()
        context["TypeOfBillChoices"] = TypeOfBillChoices

        context["current_house"] = current_house

        if selected_type_of_bill == "Bill for all clients":
            context["clients_bills"] = (current_house.client_house_other_bills
                                        .filter(month=selected_month, year=selected_year))

            clients_bills_total_amount = (
                current_house.client_house_other_bills
                .filter(month=selected_month, year=selected_year)
                .aggregate(total_amount=Coalesce(Sum("total_amount"), Value(Decimal("0.00"))))["total_amount"]
            )

            context["clients_bills_total_amount"] = clients_bills_total_amount

            context["bill"] = (
                current_house.house_other_bills
                .filter(month=selected_month, year=selected_year, type_of_bill=selected_type_of_bill)
                .first()
            )
        else:
            context.pop("clients_bills", None)

            single_bills = (
                current_house.house_other_bills
                .filter(month=selected_month,
                        year=selected_year,
                        type_of_bill=selected_type_of_bill)
            )

            calculated_total_amount = single_bills.aggregate(
                total_amount=Sum("total_amount"))["total_amount"]

            context["single_bills"] = single_bills
            context["calculated_total_amount"] = calculated_total_amount

        return context
