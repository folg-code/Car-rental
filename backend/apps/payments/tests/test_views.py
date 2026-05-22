import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="pay_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="pay_staff", password="secure-pass-123")
    return client


@pytest.mark.django_db
class TestPaymentViews:
    def test_payment_list_requires_login(self, client) -> None:
        response = client.get(reverse("payments:payment_list"))
        assert response.status_code == 302

    def test_payment_list_for_staff(self, staff_client, rental) -> None:
        response = staff_client.get(reverse("payments:payment_list"))
        assert response.status_code == 200

    def test_rental_payments_page(self, staff_client, rental) -> None:
        response = staff_client.get(
            reverse("payments:rental_payments", kwargs={"rental_id": rental.pk})
        )
        assert response.status_code == 200
        assert b"Do zaplaty" in response.content
