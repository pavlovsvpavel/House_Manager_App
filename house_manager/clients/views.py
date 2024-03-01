from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.clients.models import Client


class ClientCreateView(views.CreateView):
    queryset = Client.objects.prefetch_related("house")
    template_name = 'clients/create_client.html'
    fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied", "fixed_fee")

    def get_success_url(self):
        return reverse_lazy('list_clients_house', kwargs={'pk': self.object.house.pk})

    def form_valid(self, form):
        form.instance.house_id = self.object.house.pk

        return super().form_valid(form)


class ClientDetailsView(views.DetailView):
    queryset = Client.objects.all()
    template_name = "clients/details_client.html"


class ClientEditView(views.UpdateView):
    queryset = Client.objects.prefetch_related("house")
    template_name = 'clients/edit_client.html'
    fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied", "fixed_fee")

    def get_success_url(self):
        return reverse_lazy('list_clients_house', kwargs={'pk': self.object.house.pk})


class ClientDeleteView(views.DeleteView):
    queryset = Client.objects.prefetch_related("house")
    template_name = "clients/delete_client.html"

    def get_success_url(self):
        return reverse_lazy('list_clients_house', kwargs={'pk': self.object.house.pk})
