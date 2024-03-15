from django.http import Http404
from django.shortcuts import redirect
from django.views import generic as views

from house_manager.accounts.mixins import OwnerRequiredMixin


class IndexView(views.TemplateView):
    template_name = "common/index.html"


class DashboardView(views.TemplateView):
    template_name = "common/dashboard.html"

    # TODO: Fix unauthorized users to have access to this view
    # def get_object(self, queryset=None):
    #     if self.request.user.is_authenticated:
    #         return self.request.user
    #
    #     return None
    #
    # def dispatch(self, request, *args, **kwargs):
    #     user = self.get_object()
    #     if not user:
    #         raise Http404
    #     return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["houses"] = self.request.user.house_set.all()

        return context
