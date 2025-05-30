from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from house_manager.common.seo.sitemaps import StaticViewSitemap


sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("house_manager.common.urls")),
    path("accounts/", include("house_manager.accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("houses/", include("house_manager.houses.urls")),
    path("clients/", include("house_manager.clients.urls")),
    path("house-bills/", include("house_manager.house_bills.urls")),
    path("client-bills/", include("house_manager.client_bills.urls")),
    path('i18n/', include('django.conf.urls.i18n')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
