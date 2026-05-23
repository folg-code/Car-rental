from django.urls import path

from apps.dashboard.views import module_placeholder, panel_home

app_name = "dashboard"

urlpatterns = [
    path("", panel_home, name="home"),
    path(
        "dokumenty/",
        module_placeholder,
        {"module_name": "Dokumenty"},
        name="documents",
    ),
]
