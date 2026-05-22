from django.db.models import Q, QuerySet

from apps.bookings.models import Customer


def get_customer_by_id(customer_id: int) -> Customer | None:
    return Customer.objects.select_related("user").filter(pk=customer_id).first()


def get_customer_by_user_id(user_id: int) -> Customer | None:
    return Customer.objects.filter(user_id=user_id).first()


def list_customers(*, search: str | None = None) -> QuerySet[Customer]:
    qs = Customer.objects.select_related("user").order_by("last_name", "first_name")
    if search:
        term = search.strip()
        qs = qs.filter(
            Q(first_name__icontains=term)
            | Q(last_name__icontains=term)
            | Q(email__icontains=term)
            | Q(phone__icontains=term)
            | Q(company_name__icontains=term)
            | Q(tax_id__icontains=term)
        )
    return qs
