from django.contrib.auth import get_user_model

from apps.accounts.models import UserRole
from apps.bookings.models import Customer

User = get_user_model()


class CustomerService:
    @staticmethod
    def create(
        *,
        first_name: str,
        last_name: str,
        email: str = "",
        phone: str = "",
        company_name: str = "",
        tax_id: str = "",
        street: str = "",
        city: str = "",
        postal_code: str = "",
        country: str = "PL",
        notes: str = "",
        user_id: int | None = None,
    ) -> Customer:
        if user_id is not None:
            user = User.objects.filter(pk=user_id).first()
            if user is None:
                msg = f"User {user_id} does not exist."
                raise ValueError(msg)
            if user.role != UserRole.CUSTOMER:
                msg = "Powiazany uzytkownik musi miec role customer."
                raise ValueError(msg)

        customer = Customer(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company_name=company_name,
            tax_id=tax_id,
            street=street,
            city=city,
            postal_code=postal_code,
            country=country,
            notes=notes,
        )
        customer.save()
        return customer
