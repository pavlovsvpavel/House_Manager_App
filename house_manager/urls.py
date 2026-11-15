from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import path, include

from house_manager.common.seo.sitemaps import StaticViewSitemap


def chrome_devtools_probe(request):
    """Chrome DevTools requests this path whenever DevTools is open,
    probing for its workspace config. Answer 204 instead of the loud
    debug 404 page; the file is intentionally not provided."""
    return HttpResponse(status=204)


sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("house_manager.common.urls")),
    path("accounts/", include("house_manager.accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("houses/", include("house_manager.houses.urls")),
    path("houses/<int:house_pk>/clients/", include("house_manager.clients.urls")),
    path("houses/<int:house_pk>/clients/<int:client_pk>/", include("house_manager.client_bills.urls")),
    path("houses/<int:house_pk>/bills/", include("house_manager.house_bills.urls")),
    path('i18n/', include('django.conf.urls.i18n')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_probe),
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
