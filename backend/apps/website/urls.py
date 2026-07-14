from django.urls import path

from apps.website import views

app_name = "website"

urlpatterns = [
    path("", views.landing, name="home"),
]
