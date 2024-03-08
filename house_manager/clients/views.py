from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic as views

from house_manager.clients.models import Client
from house_manager.houses.models import House

UserModel = get_user_model()


class ClientCreateView(views.CreateView):
    queryset = Client.objects.all()
    template_name = 'clients/create_client.html'
    fields = ("family_name", "floor", "apartment", "number_of_people", "is_using_lift", "is_occupied", "fixed_fee")

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.house.pk})

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.get_object()
        context['house'] = house
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)

        form.instance.house = self.get_object()
        form.instance.user = self.request.user

        return form


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
