from django.urls import path

from apps.website import views

app_name = "website"

urlpatterns = [
    path("", views.landing, name="home"),
    path("flota/", views.fleet_list, name="fleet_list"),
    path("flota/dostepnosc/", views.availability_search, name="availability_search"),
    path("wycena/", views.price_quote, name="price_quote"),
    path("rezerwacja/", views.public_booking, name="public_booking"),
    path(
        "rezerwacja/potwierdzenie/",
        views.booking_confirmation,
        name="booking_confirmation",
    ),
    path("regulamin/", views.terms, name="terms"),
    path("kontakt/", views.contact, name="contact"),
    path("faq/", views.faq, name="faq"),
]
