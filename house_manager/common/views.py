from django.views import generic as views

from house_manager.houses.models import House


class IndexView(views.TemplateView):
    template_name = "common/index.html"


class DashboardView(views.TemplateView):
    template_name = "common/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["houses"] = self.request.user.house_set.all()

        return context

