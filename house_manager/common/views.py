from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render
from django.views import generic as views

from house_manager.client_bills.models import ClientMonthlyBill
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

        houses = list(
            House.objects.filter(user=self.request.user)
            .annotate(clients_count=Count("clients", distinct=True))
        )

        # Unpaid totals are computed in a separate aggregate query: combining
        # two reverse joins (clients + bills) in one queryset fans out rows
        # and multiplies the Sum.
        unpaid_stats = (
            ClientMonthlyBill.objects
            .filter(house__in=[h.pk for h in houses], is_paid=False)
            .values("house_id")
            .annotate(unpaid_count=Count("id"), unpaid_total=Sum("total_amount"))
        )
        stats_by_house = {row["house_id"]: row for row in unpaid_stats}

        for house in houses:
            stats = stats_by_house.get(house.pk)
            house.unpaid_bills_count = stats["unpaid_count"] if stats else 0
            house.unpaid_bills_total = stats["unpaid_total"] if stats else Decimal("0.00")

        context["houses"] = houses

        return context


def about_view(request):
    return render(request, "common/about.html")
