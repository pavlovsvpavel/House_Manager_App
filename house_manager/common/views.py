from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views
from django.shortcuts import render
from house_manager.common.mixins import MonthChoices, YearChoices
from house_manager.house_bills.models import TypeOfBillChoices
from house_manager.houses.models import House


class IndexView(views.TemplateView):
    template_name = "common/index.html"


class DashboardView(views.TemplateView):
    template_name = "common/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return self.render_to_response(self.get_context_data(**kwargs))

        return redirect("login_user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["houses"] = self.request.user.house_set.all()

        return context


def about_view(request):
    return render(request, "common/about.html")


class ReportMonthlyBillView(views.DetailView):
    template_name = "common/reports_bills.html"
    success_url = reverse_lazy("reports_bills")
    queryset = House.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_house = get_object_or_404(House, pk=self.kwargs["pk"])

        selected_month = self.request.GET.get("month")
        selected_year = self.request.GET.get("year")

        context["MonthChoices"] = MonthChoices
        context["YearChoices"] = YearChoices.previous_and_next_years()

        context["current_house"] = current_house

        context["bill"] = (current_house.house_monthly_bills
                           .filter(month=selected_month, year=selected_year).first())

        context["clients_bills"] = (current_house.client_house_monthly_bills
                                    .filter(month=selected_month, year=selected_year))

        return context


class ReportOtherBillView(views.DetailView):
    template_name = "common/reports_other_bills.html"
    success_url = reverse_lazy("reports_other_bills")
    queryset = House.objects.all()

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
                total_amount=Sum('total_amount'))['total_amount']

            context["single_bills"] = single_bills
            context["calculated_total_amount"] = calculated_total_amount

        return context
