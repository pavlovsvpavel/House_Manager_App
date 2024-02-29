from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.accounts.mixins import GetProfileMixin
from house_manager.clients.models import Client
from house_manager.houses.models import House


class HouseCreateView(GetProfileMixin, views.CreateView):
    queryset = House.objects.all()
    template_name = "houses/create_house.html"
    fields = ("town", "address", "building_number", "entrance")
    success_url = reverse_lazy("index")

    # TODO: Fix the userprofile to be taken dynamically
    def form_valid(self, form):
        form.instance.owner_id = self.get_profile().pk

        return super().form_valid(form)


class HouseDetailsView(GetProfileMixin, views.DetailView):
    queryset = House.objects.all()
    template_name = "houses/details_house.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["clients"] = Client.objects.all()

        return context
