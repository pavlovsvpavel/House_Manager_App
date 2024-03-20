from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views
from django.utils.translation import gettext as _

from house_manager.client_bills.helpers.calculate_fees import calculate_fees
from house_manager.client_bills.helpers.calculate_fees_other_bills import calculate_fees_other_bills
from house_manager.clients.models import Client
from house_manager.house_bills.forms import HouseMonthlyBillForm, HouseOtherBillForm
from house_manager.house_bills.helpers.subtract_amount_from_balance import subtract_amount_from_house_balance
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill
from house_manager.houses.mixins import GetUserAndHouseInstanceMixin
from house_manager.houses.models import House


class HouseBaseBillCreateView(GetUserAndHouseInstanceMixin, views.CreateView):
    queryset = None
    template_name = None
    form_class = None

    def get_success_url(self):
        selected_house_pk = self.request.session.get("selected_house")

        return reverse_lazy('details_house', kwargs={'pk': selected_house_pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get("selected_house")

        context['house_id'] = house_id
        context['clients'] = Client.objects.filter(house=house_id)

        return context


class HouseMonthlyBillCreateView(HouseBaseBillCreateView):
    queryset = HouseMonthlyBill.objects.select_related('house')
    template_name = "house_bills/create_house_bills.html"
    form_class = HouseMonthlyBillForm

    # def get_success_url(self):
    #     selected_house_pk = self.request.session.get("selected_house")
    #
    #     return reverse_lazy('details_house', kwargs={'pk': selected_house_pk})
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     house_id = self.request.session.get("selected_house")
    #
    #     context['house_id'] = house_id
    #     context['clients'] = Client.objects.filter(house=house_id)
    #
    #     return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            current_year = form.instance.year
            current_month = form.instance.month
            house_id = form.instance.house_id
            user_id = self.request.user.pk
            calculate_fees(house_id, current_year, current_month, user_id)

            return response

        except IntegrityError as e:
            error_message = _("Bill with those month and year already exists.")
            form.add_error(None, error_message)

            return self.form_invalid(form)


class HouseOtherBillCreateView(HouseBaseBillCreateView):
    queryset = HouseOtherBill.objects.select_related('house')
    template_name = "house_bills/create_other_bill.html"
    form_class = HouseOtherBillForm

    # def get_success_url(self):
    #     selected_house_pk = self.request.session.get("selected_house")
    #
    #     return reverse_lazy('details_house', kwargs={'pk': selected_house_pk})
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     house_id = self.request.session.get("selected_house")
    #
    #     context['house_id'] = house_id
    #     context['clients'] = Client.objects.filter(house=house_id)
    #
    #     return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            current_year = form.instance.year
            current_month = form.instance.month
            house_id = form.instance.house_id
            user_id = self.request.user.pk
            calculate_fees_other_bills(house_id, current_year, current_month, user_id)

            return response

        except IntegrityError as e:
            error_message = _("Bill with those month and year already exists.")
            form.add_error(None, error_message)

            return self.form_invalid(form)


class CurrentHouseBaseBillDetailView(views.DetailView):
    template_name = None

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["house_bills"] = self.get_type_of_house_bills()
        return context

    def get_type_of_house_bills(self):
        raise NotImplementedError("Subclasses must implement get_type_of_house_bills()")


class CurrentHouseMonthlyBillDetailView(CurrentHouseBaseBillDetailView):
    template_name = "house_bills/list_house_bills.html"

    def get_type_of_house_bills(self):
        return self.object.house_monthly_bills.all()

    # def get_object(self, queryset=None):
    #     return get_object_or_404(House, pk=self.kwargs['pk'])
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #
    #     context["house_bills"] = self.object.house_monthly_bills.all()
    #
    #     return context


class CurrentHouseOtherBillDetailView(CurrentHouseBaseBillDetailView):
    template_name = "house_bills/list_other_house_bills.html"

    def get_type_of_house_bills(self):
        return self.object.house_other_bills.all()
    # def get_object(self, queryset=None):
    #     return get_object_or_404(House, pk=self.kwargs['pk'])
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #
    #     context["house_bills"] = self.object.house_other_bills.all()
    #
    #     return context


class HouseBaseBillEditView(views.UpdateView):
    queryset = None
    template_name = None
    success_url_name = None
    fields = ("is_paid",)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name, kwargs={"pk": self.object.house.pk})

    def get_template_name(self):
        return [self.template_name]

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


class HouseMonthlyBillEditView(HouseBaseBillEditView):
    queryset = HouseMonthlyBill.objects.prefetch_related("house")
    template_name = "house_bills/details_house_bills.html"
    success_url_name = "list_house_bills"

    # fields = ("is_paid",)

    # def get_success_url(self):
    #     return reverse_lazy("list_house_bills", kwargs={"pk": self.object.house.pk})

    # def form_valid(self, form):
    #     if not form.cleaned_data['is_paid']:
    #         return self.form_invalid(form)
    #     else:
    #         house_id = form.instance.house_id
    #         bill_id = form.instance.id
    #         type_of_bill = self.queryset.model
    #         subtract_amount_from_house_balance(type_of_bill, house_id, bill_id)
    #         return super().form_valid(form)
    #
    # def get_form(self, form_class=None):
    #     form = super().get_form(form_class)
    #     if form.instance.is_paid:
    #         form.fields["is_paid"].disabled = True
    #     return form


class HouseOtherBillEditView(HouseBaseBillEditView):
    queryset = HouseOtherBill.objects.prefetch_related("house")
    template_name = "house_bills/details_other_house_bills.html"
    success_url_name = "list_other_house_bills"
    # fields = ("is_paid",)

    # def get_success_url(self):
    #     return reverse_lazy("list_other_house_bills", kwargs={"pk": self.object.house.pk})
    #
    # def form_valid(self, form):
    #     if not form.cleaned_data['is_paid']:
    #         return self.form_invalid(form)
    #     else:
    #         house_id = form.instance.house_id
    #         bill_id = form.instance.id
    #         type_of_bill = self.queryset.model
    #         subtract_amount_from_house_balance(type_of_bill, house_id, bill_id)
    #         return super().form_valid(form)
    #
    # def get_form(self, form_class=None):
    #     form = super().get_form(form_class)
    #     if form.instance.is_paid:
    #         form.fields["is_paid"].disabled = True
    #     return form
