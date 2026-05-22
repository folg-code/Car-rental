from django.urls import path

from apps.dashboard.views import module_placeholder, panel_home

app_name = "dashboard"

urlpatterns = [
    path("", panel_home, name="home"),
    path(
        "rezerwacje/",
        module_placeholder,
        {"module_name": "Rezerwacje"},
        name="bookings",
    ),
    path(
        "operacje/",
        module_placeholder,
        {"module_name": "Operacje"},
        name="operations",
    ),
    path(
        "platnosci/",
        module_placeholder,
        {"module_name": "Platnosci"},
        name="payments",
    ),
    path(
        "dokumenty/",
        module_placeholder,
        {"module_name": "Dokumenty"},
        name="documents",
    ),
]
