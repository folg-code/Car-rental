from django.urls import path

from apps.pricing import views

app_name = "pricing"

urlpatterns = [
    path("", views.price_list_list, name="price_list_list"),
    path("nowy/", views.price_list_create, name="price_list_create"),
    path("<int:pk>/", views.price_list_detail, name="price_list_detail"),
    path("<int:pk>/edycja/", views.price_list_edit, name="price_list_edit"),
]
