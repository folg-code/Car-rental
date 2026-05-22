from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    path("", views.payment_list, name="payment_list"),
    path("wynajem/<int:rental_id>/", views.rental_payments, name="rental_payments"),
    path(
        "wynajem/<int:rental_id>/kaucja/",
        views.record_deposit_quick,
        name="record_deposit_quick",
    ),
    path(
        "wynajem/<int:rental_id>/zwrot-kaucji/",
        views.refund_deposit_quick,
        name="refund_deposit_quick",
    ),
]
