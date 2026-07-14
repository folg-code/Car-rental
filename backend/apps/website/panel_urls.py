from django.urls import path

from apps.website import views_support

app_name = "website_support"

urlpatterns = [
    path("", views_support.chat_session_list, name="session_list"),
    path(
        "<int:session_id>/",
        views_support.chat_session_detail,
        name="session_detail",
    ),
]
