from django.views import generic as views

from house_manager.houses.models import House


class IndexView(views.TemplateView):
    template_name = "common/index.html"


class DashboardView(views.TemplateView):
    queryset = House.objects.all()
    template_name = "common/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["houses"] = House.objects.all()

        return context

