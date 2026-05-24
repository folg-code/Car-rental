from django.urls import path

from apps.documents import views

app_name = "documents"

urlpatterns = [
    path("", views.document_list, name="home"),
    path(
        "wynajem/<int:rental_id>/",
        views.rental_documents,
        name="rental",
    ),
    path(
        "<uuid:document_uuid>/pobierz/",
        views.document_download,
        name="download",
    ),
]
