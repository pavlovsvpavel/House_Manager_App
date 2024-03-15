from django.apps import AppConfig


class HousesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'house_manager.houses'

    # def ready(self):
    #     return 'house_manager.houses.middleware.HousesMiddleware'
