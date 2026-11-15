from decimal import Decimal

from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.views import generic as views

from house_manager.client_bills.models import ClientMonthlyBill, ClientOtherBill
from house_manager.house_bills.models import HouseMonthlyBill, HouseOtherBill
from house_manager.houses.models import House


class IndexView(views.TemplateView):
    template_name = "common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user

        return context


class DashboardView(views.TemplateView):
    template_name = "common/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return self.render_to_response(self.get_context_data(**kwargs))

        return redirect("login_user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        houses = list(House.objects.filter(user=self.request.user))

        # Each bill type aggregates in its own query: combining reverse joins
        # (clients + bills) in one queryset fans out rows and multiplies the Sum.
        house_ids = [h.pk for h in houses]

        def stats_by_house(queryset):
            rows = queryset.values("house_id").annotate(
                bills_count=Count("id"), bills_total=Sum("total_amount"))
            return {row["house_id"]: row for row in rows}

        client_monthly = stats_by_house(
            ClientMonthlyBill.objects.filter(house__in=house_ids, is_paid=False))
        client_other = stats_by_house(
            ClientOtherBill.objects.filter(house__in=house_ids, is_paid=False))
        client_monthly_paid = stats_by_house(
            ClientMonthlyBill.objects.filter(house__in=house_ids, is_paid=True))
        client_other_paid = stats_by_house(
            ClientOtherBill.objects.filter(house__in=house_ids, is_paid=True))
        house_monthly = stats_by_house(
            HouseMonthlyBill.objects.filter(house__in=house_ids, is_paid=False))
        house_other = stats_by_house(
            HouseOtherBill.objects.filter(house__in=house_ids, is_paid=False))

        for house in houses:
            cm = client_monthly.get(house.pk, {})
            co = client_other.get(house.pk, {})
            cmp_ = client_monthly_paid.get(house.pk, {})
            cop = client_other_paid.get(house.pk, {})
            hm = house_monthly.get(house.pk, {})
            ho = house_other.get(house.pk, {})

            house.unpaid_bills_count = cm.get("bills_count", 0) + co.get("bills_count", 0)
            house.unpaid_bills_total = (
                cm.get("bills_total") or Decimal("0.00")
            ) + (co.get("bills_total") or Decimal("0.00"))
            house.paid_bills_count = cmp_.get("bills_count", 0) + cop.get("bills_count", 0)
            house.unpaid_house_monthly_total = hm.get("bills_total") or Decimal("0.00")
            house.unpaid_house_other_total = ho.get("bills_total") or Decimal("0.00")

        context["houses"] = houses

        return context


def about_view(request):
    return render(request, "common/about.html")
