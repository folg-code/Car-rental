from django.urls import path

from apps.payments import views_webhook

app_name = "payments_webhook"

urlpatterns = [
    path("", views_webhook.payment_webhook, name="webhook"),
]
