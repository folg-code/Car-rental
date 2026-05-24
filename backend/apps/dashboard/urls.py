from django.urls import path

from apps.dashboard.views import panel_home

app_name = "dashboard"

urlpatterns = [
    path("", panel_home, name="home"),
]
