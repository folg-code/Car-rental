import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import Customer
from apps.bookings.services.customer import CustomerService


@pytest.mark.django_db
class TestCustomerModel:
    def test_create_with_email(self) -> None:
        customer = Customer(
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
        )
        customer.save()
        assert customer.pk is not None
        assert customer.full_name == "Jan Kowalski"

    def test_requires_email_or_phone(self) -> None:
        customer = Customer(first_name="Jan", last_name="Kowalski")
        with pytest.raises(ValidationError):
            customer.save()


@pytest.mark.django_db
class TestCustomerService:
    def test_create_customer(self) -> None:
        customer = CustomerService.create(
            first_name="Anna",
            last_name="Nowak",
            email="anna@example.com",
            phone="+48123456789",
        )
        assert Customer.objects.filter(pk=customer.pk).exists()

    def test_link_customer_user_requires_customer_role(self) -> None:
        staff = UserService.create_user(
            username="staff1",
            password="secure-pass-123",
            role=UserRole.EMPLOYEE,
        )
        with pytest.raises(ValueError, match="role customer"):
            CustomerService.create(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                user_id=staff.pk,
            )
