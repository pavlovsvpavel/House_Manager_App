from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic as views

from house_manager.houses.decorators import get_current_house_instance
from house_manager.houses.models import House


class HouseCreateView(views.CreateView):
    queryset = House.objects.all()
    template_name = "houses/create_house.html"
    fields = ("town", "address", "building_number", "entrance", "money_balance")
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user

        return super().form_valid(form)


@method_decorator(get_current_house_instance, name='dispatch')
class HouseDetailsView(views.DetailView):
    queryset = House.objects.prefetch_related("house_monthly_bills")
    template_name = "houses/details_house.html"

    def get(self, request, *args, **kwargs):
        selected_house_id = self.kwargs.get('pk')

        selected_house = House.objects.get(id=selected_house_id)
        request.session['selected_house'] = selected_house.pk

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_apartments = House.objects.total_apartments(house_id=self.kwargs.get('pk'))
        total_people = House.objects.total_people(house_id=self.kwargs.get('pk'))
        total_people_using_lift = House.objects.total_people_using_lift(house_id=self.kwargs.get('pk'))

        context['total_apartments'] = total_apartments
        context['total_people'] = total_people
        context['total_people_using_lift'] = total_people_using_lift

        return context


class HouseClientsDetailsView(views.DetailView):
    template_name = "houses/list_house_clients.html"

    def get_object(self, queryset=None):
        return get_object_or_404(House, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["clients"] = self.object.clients.all()

        return context


class HouseEditView(views.UpdateView):
    queryset = House.objects.all()
    template_name = "houses/edit_house.html"
    fields = ("town", "address", "building_number", "entrance", "money_balance")

    def get_success_url(self):
        return reverse_lazy('details_house', kwargs={'pk': self.object.pk})


class HouseDeleteView(views.DeleteView):
    queryset = House.objects.all()
    template_name = "houses/delete_house.html"

    def get_success_url(self):
        return reverse_lazy('dashboard')

