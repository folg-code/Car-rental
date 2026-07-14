from django.urls import path

from apps.website import views_portal

app_name = "customer_portal"

urlpatterns = [
    path("", views_portal.portal_home, name="home"),
    path("rezerwacje/", views_portal.reservation_list, name="reservation_list"),
    path(
        "rezerwacje/<int:reservation_id>/",
        views_portal.reservation_detail,
        name="reservation_detail",
    ),
    path(
        "dokumenty/<uuid:document_uuid>/pobierz/",
        views_portal.document_download,
        name="document_download",
    ),
]
