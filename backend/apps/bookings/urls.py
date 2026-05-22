from django.urls import path

from apps.bookings import views

app_name = "bookings"

urlpatterns = [
    path("", views.customer_list, name="customer_list"),
    path("nowy/", views.customer_create, name="customer_create"),
    path("<int:pk>/", views.customer_detail, name="customer_detail"),
    path("<int:pk>/edycja/", views.customer_edit, name="customer_edit"),
    path("<int:pk>/usun/", views.customer_delete, name="customer_delete"),
]
