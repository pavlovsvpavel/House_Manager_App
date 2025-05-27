from django.conf import settings


def global_settings(request):
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None),
        'debug': settings.DEBUG,
    }
