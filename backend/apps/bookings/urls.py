from django.urls import path

from apps.bookings import views

app_name = "bookings"

urlpatterns = [
    path("", views.reservation_list, name="reservation_list"),
    path("nowa/", views.reservation_create, name="reservation_create"),
    path("<int:pk>/", views.reservation_detail, name="reservation_detail"),
    path("<int:pk>/edycja/", views.reservation_edit, name="reservation_edit"),
    path("<int:pk>/potwierdz/", views.reservation_confirm, name="reservation_confirm"),
    path("<int:pk>/wygas/", views.reservation_expire, name="reservation_expire"),
    path("<int:pk>/anuluj/", views.reservation_cancel, name="reservation_cancel"),
    path("klienci/", views.customer_list, name="customer_list"),
    path("klienci/nowy/", views.customer_create, name="customer_create"),
    path("klienci/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("klienci/<int:pk>/edycja/", views.customer_edit, name="customer_edit"),
    path("klienci/<int:pk>/usun/", views.customer_delete, name="customer_delete"),
]
