from django.urls import path

from apps.dashboard.views import financial_report, panel_entry, panel_home

app_name = "dashboard"

urlpatterns = [
    path("", panel_entry, name="entry"),
    path("admin/", panel_home, name="home"),
    path("raporty/", financial_report, name="financial_report"),
]
