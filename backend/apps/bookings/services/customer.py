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

    @staticmethod
    def get_or_create_for_public_booking(
        *,
        first_name: str,
        last_name: str,
        email: str = "",
        phone: str = "",
    ) -> tuple[Customer, bool]:
        """Dopasuj istniejacego klienta po emailu lub telefonie albo utworz nowego."""
        normalized_email = email.strip().lower()
        normalized_phone = phone.strip()
        if normalized_email:
            existing = Customer.objects.filter(email__iexact=normalized_email).first()
            if existing is not None:
                return existing, False
        if normalized_phone:
            existing = Customer.objects.filter(phone=normalized_phone).first()
            if existing is not None:
                return existing, False
        customer = CustomerService.create(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=normalized_email,
            phone=normalized_phone,
        )
        return customer, True

    @staticmethod
    def get_or_create_portal_user(customer: Customer) -> User:
        """Zapewnij konto customer bez hasla (logowanie kodem OTP)."""
        if customer.user_id is not None:
            user = customer.user
            if user.role != UserRole.CUSTOMER:
                raise ValueError("Powiazany uzytkownik musi miec role customer.")
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            return user

        email = (customer.email or "").strip().lower()
        username = f"customer-{customer.pk}"
        user = User.objects.filter(username=username).first()
        if user is None and email:
            user = User.objects.filter(
                email__iexact=email, role=UserRole.CUSTOMER
            ).first()

        if user is None:
            user = User(
                username=username,
                email=email,
                first_name=customer.first_name,
                last_name=customer.last_name,
                role=UserRole.CUSTOMER,
                is_staff=False,
                is_superuser=False,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
        else:
            user.role = UserRole.CUSTOMER
            user.email = email or user.email
            user.first_name = customer.first_name or user.first_name
            user.last_name = customer.last_name or user.last_name
            user.is_active = True
            user.set_unusable_password()
            user.save()

        customer.user = user
        customer.save(update_fields=["user", "updated_at"])
        return user
