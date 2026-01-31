from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic as views
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.mixins import CheckForLoggedInUserMixin
from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.client_bills.helpers.calculate_fees_other_bills import calculate_fees_other_bills
from house_manager.client_bills.helpers.calculate_fixed_bills import calculate_fixed_client_bills
from house_manager.client_bills.models import ClientMonthlyBill
from house_manager.clients.models import Client
from house_manager.common.mixins import MonthChoices, YearChoices
from house_manager.house_bills.forms import HouseMonthlyBillForm, HouseOtherBillForm, HouseFixedBillForm
from house_manager.house_bills.helpers.filter_bills_by_payment_status import filter_bills_by_payment_status
from house_manager.house_bills.helpers.subtract_amount_from_balance import subtract_amount_from_house_balance
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill, TypeOfBillChoices
from house_manager.houses.decorators import get_current_house_id
from house_manager.houses.mixins import GetHouseAndUserMixin
from house_manager.houses.models import House, HouseCalculationsOptions


class HouseBaseBillCreateView(CheckForLoggedInUserMixin, GetHouseAndUserMixin, views.CreateView):
    template_name = None
    form_class = None
    action_url = None
    title = None

    @property
    def current_house(self):
        house_id = self.request.session.get("selected_house")

        if house_id:
            return get_object_or_404(House, pk=house_id)
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.current_house
        context['house'] = house

        if house:
            context['clients'] = Client.objects.filter(house=house)

        context['action_url'] = self.action_url
        context["title"] = self.title
        return context

    def get_success_url(self):
        house_id = self.request.session.get("selected_house")
        return reverse_lazy('details_house', kwargs={'pk': house_id})

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
    action_url = reverse_lazy("create_house_bills")
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
    action_url = reverse_lazy("create_other_bill")
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
    action_url = reverse_lazy("create_fixed_bill")
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


@method_decorator(get_current_house_id, name='dispatch')
class CurrentHouseBaseBillDetailView(CheckForLoggedInUserMixin, views.DetailView):
    template_name = None

    def get_object(self, queryset=None):
        return self.request.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get("selected_house")

        is_paid = self.request.GET.get('is_paid', None)
        month = self.request.GET.get('month', None)

        if house_id:
            current_house = self.get_object()
            if current_house.id != house_id:
                raise PermissionDenied(_("Bills not found in selected house."))

            house_bills = self.get_type_of_house_bills()

            if is_paid is not None:
                house_bills = filter_bills_by_payment_status(house_bills, is_paid, month)

            context["house_bills"] = house_bills
            context["MonthChoices"] = MonthChoices

        return context

    def get_type_of_house_bills(self):
        raise NotImplementedError("Subclasses must implement get_type_of_house_bills()")


class CurrentHouseMonthlyBillDetailView(CurrentHouseBaseBillDetailView):
    template_name = "house_bills/list_house_bills.html"

    def get_type_of_house_bills(self):
        return self.object.house_monthly_bills.order_by("is_paid", "-year", "-month").all()


class CurrentHouseOtherBillDetailView(CurrentHouseBaseBillDetailView):
    template_name = "house_bills/list_other_house_bills.html"

    def get_type_of_house_bills(self):
        return self.object.house_other_bills.order_by("is_paid", "-year", "-month").all()


class HouseBaseBillEditView(CheckForLoggedInUserMixin, views.UpdateView):
    queryset = None
    template_name = None
    success_url_name = None
    fields = ("is_paid",)

    def get_template_name(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get("selected_house")
        current_house = self.object.house.pk

        if current_house != house_id:
            raise PermissionDenied(_("Bills not found in selected house."))

        return context

    def form_valid(self, form):
        if not form.cleaned_data['is_paid']:
            return self.form_invalid(form)
        else:
            house_id = form.instance.house_id
            bill_id = form.instance.id
            type_of_bill = self.queryset.model
            subtract_amount_from_house_balance(type_of_bill, house_id, bill_id)
            return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form.instance.is_paid:
            form.fields["is_paid"].disabled = True
        return form

    def get_success_url(self):
        return reverse_lazy(self.success_url_name, kwargs={"pk": self.object.house.pk})


class HouseMonthlyBillEditView(HouseBaseBillEditView):
    queryset = HouseMonthlyBill.objects.prefetch_related("house")
    template_name = "house_bills/edit_house_bills.html"
    success_url_name = "list_house_bills"


class HouseOtherBillEditView(HouseBaseBillEditView):
    queryset = HouseOtherBill.objects.prefetch_related("house")
    template_name = "house_bills/edit_other_house_bills.html"
    success_url_name = "list_other_house_bills"


@method_decorator(get_current_house_id, name='dispatch')
class ReportMonthlyBillView(views.DetailView):
    template_name = "common/reports_bills.html"
    success_url = reverse_lazy("reports_bills")

    def get_object(self, queryset=None):
        return self.request.selected_house

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


@method_decorator(get_current_house_id, name='dispatch')
class ReportOtherBillView(views.DetailView):
    template_name = "common/reports_other_bills.html"
    success_url = reverse_lazy("reports_other_bills")

    def get_object(self, queryset=None):
        return self.request.selected_house

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_house = get_object_or_404(House, pk=self.kwargs["pk"])

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
