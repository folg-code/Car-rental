from django.db.models import QuerySet

from apps.bookings.models import Customer


def get_customer_by_id(customer_id: int) -> Customer | None:
    return Customer.objects.filter(pk=customer_id).first()


def get_customer_by_user_id(user_id: int) -> Customer | None:
    return Customer.objects.filter(user_id=user_id).first()


def list_customers() -> QuerySet[Customer]:
    return Customer.objects.select_related("user").order_by("last_name", "first_name")
