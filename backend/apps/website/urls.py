from django.urls import path

from apps.website import views

app_name = "website"

urlpatterns = [
    path("", views.landing, name="home"),
    path("flota/", views.fleet_list, name="fleet_list"),
    path("flota/dostepnosc/", views.availability_search, name="availability_search"),
    path("oferta/", views.car_offer, name="car_offer"),
    path("wycena/", views.price_quote, name="price_quote"),
    path("rezerwacja/", views.public_booking, name="public_booking"),
    path(
        "rezerwacja/potwierdzenie/",
        views.booking_confirmation,
        name="booking_confirmation",
    ),
    path(
        "rezerwacja/<int:reservation_id>/potwierdzenie/",
        views.booking_confirmation_by_id,
        name="booking_confirmation_by_id",
    ),
    path(
        "rezerwacja/<int:reservation_id>/platnosc/",
        views.start_payment,
        name="start_payment",
    ),
    path(
        "rezerwacja/<int:reservation_id>/platnosc/sukces/",
        views.payment_success,
        name="payment_success",
    ),
    path("platnosc/mock/", views.mock_payment_checkout, name="mock_payment_checkout"),
    path("regulamin/", views.terms, name="terms"),
    path("kontakt/", views.contact, name="contact"),
    path("faq/", views.faq, name="faq"),
    path("asystent/", views.consultant, name="consultant"),
    path("asystent/wiadomosc/", views.consultant_message, name="consultant_message"),
]
