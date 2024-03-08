from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views

# from house_manager.accounts.mixins import GetProfileMixin
from house_manager.houses.models import House


class HouseCreateView(views.CreateView):
    queryset = House.objects.all()
    template_name = "houses/create_house.html"
    fields = ("town", "address", "building_number", "entrance")
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user

        return super().form_valid(form)


class HouseDetailsView(views.DetailView):
    queryset = House.objects.all()
    template_name = "houses/details_house.html"


class HouseClientsDetailsView(views.DetailView):

    template_name = "houses/list_clients_house.html"

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["clients"] = self.object.clients.all()

        return context


class HouseEditView(views.UpdateView):
    queryset = House.objects.all()
    template_name = "houses/edit_house.html"
    fields = ("town", "address", "building_number", "entrance")

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.pk})
