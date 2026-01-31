from decimal import Decimal
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic as views
from django.shortcuts import render

from house_manager.common.mixins import MonthChoices, YearChoices
from house_manager.house_bills.models import TypeOfBillChoices
from house_manager.houses.decorators import get_current_house_id
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

        context["houses"] = self.request.user.house_set.all()

        return context


def about_view(request):
    return render(request, "common/about.html")
