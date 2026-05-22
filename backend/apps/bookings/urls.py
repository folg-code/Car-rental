from django.urls import path

from apps.bookings import views

app_name = "bookings"

urlpatterns = [
    path("", views.reservation_list, name="reservation_list"),
    path("nowa/", views.reservation_create, name="reservation_create"),
    path("wynajmy/", views.rental_list, name="rental_list"),
    path("wynajmy/<int:pk>/", views.rental_detail, name="rental_detail"),
    path("wynajmy/<int:pk>/start/", views.rental_start, name="rental_start"),
    path("wynajmy/<int:pk>/zwrot/", views.rental_return, name="rental_return"),
    path("wynajmy/<int:pk>/zamknij/", views.rental_close, name="rental_close"),
    path("wynajmy/<int:pk>/anuluj/", views.rental_cancel, name="rental_cancel"),
    path("klienci/", views.customer_list, name="customer_list"),
    path("klienci/nowy/", views.customer_create, name="customer_create"),
    path("klienci/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("klienci/<int:pk>/edycja/", views.customer_edit, name="customer_edit"),
    path("klienci/<int:pk>/usun/", views.customer_delete, name="customer_delete"),
    path("<int:pk>/", views.reservation_detail, name="reservation_detail"),
    path("<int:pk>/edycja/", views.reservation_edit, name="reservation_edit"),
    path(
        "<int:pk>/przelicz-cene/",
        views.reservation_recalculate_price,
        name="reservation_recalculate_price",
    ),
    path("<int:pk>/potwierdz/", views.reservation_confirm, name="reservation_confirm"),
    path("<int:pk>/wygas/", views.reservation_expire, name="reservation_expire"),
    path("<int:pk>/anuluj/", views.reservation_cancel, name="reservation_cancel"),
    path(
        "<int:pk>/utworz-wynajem/",
        views.reservation_convert_to_rental,
        name="reservation_convert_to_rental",
    ),
]
