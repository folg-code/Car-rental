from django.urls import path

from apps.website import views_portal, views_portal_auth

app_name = "customer_portal"

urlpatterns = [
    path("", views_portal.portal_home, name="home"),
    path(
        "logowanie-kodem/",
        views_portal_auth.portal_login_request,
        name="otp_request",
    ),
    path(
        "logowanie-kodem/potwierdz/",
        views_portal_auth.portal_login_verify,
        name="otp_verify",
    ),
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
