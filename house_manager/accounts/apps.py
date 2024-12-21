from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'house_manager.accounts'

    def ready(self):
        import house_manager.accounts.signals
