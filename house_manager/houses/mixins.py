from house_manager.houses.models import House


class GetHouseAndUserMixin:
    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        house_id = self.request.session.get("selected_house")
        if house_id:
            house = House.objects.get(pk=house_id)
            form.instance.house = house
        form.instance.user = self.request.user

        return form
