from django.urls import path

from apps.dashboard.views import financial_report, panel_home

app_name = "dashboard"

urlpatterns = [
    path("", panel_home, name="home"),
    path("raporty/", financial_report, name="financial_report"),
]
