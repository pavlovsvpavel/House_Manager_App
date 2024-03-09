from house_manager.houses.models import House


class GetCurrentHouseInstanceMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.request.session.get('selected_house_id')
        if house_id:
            context['house'] = House.objects.get(pk=house_id)
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        house_id = self.request.session.get('selected_house_id')
        if house_id:
            house = House.objects.get(pk=house_id)
            form.instance.house = house
        form.instance.user = self.request.user

        return form
