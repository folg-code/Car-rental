"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.health_views import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("", include("apps.website.urls")),
    path("admin/", admin.site.urls),
    path("konto/", include(("apps.website.portal_urls", "customer_portal"))),
    path("konto/", include("apps.accounts.urls")),
    path("panel/", include("apps.dashboard.urls")),
    path("panel/flota/", include("apps.fleet.urls")),
    path("panel/rezerwacje/", include("apps.bookings.urls")),
    path("panel/cenniki/", include("apps.pricing.urls")),
    path("panel/platnosci/", include("apps.payments.urls")),
    path(
        "platnosci/webhook/",
        include(("apps.payments.webhook_urls", "payments_webhook")),
    ),
    path("panel/operacje/", include("apps.operations.urls")),
    path("panel/dokumenty/", include("apps.documents.urls")),
    path("panel/asystent/", include(("apps.website.panel_urls", "website_support"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
