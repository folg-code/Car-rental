import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import Customer


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="bookings_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="bookings_staff", password="secure-pass-123")
    return client


@pytest.fixture
def sample_customer(db) -> Customer:
    return Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@example.com",
        phone="+48111111111",
    )


@pytest.mark.django_db
class TestCustomerViews:
    def test_customer_list_requires_login(self, client) -> None:
        response = client.get(reverse("bookings:customer_list"))
        assert response.status_code == 302

    def test_customer_list_for_staff(
        self, staff_client, sample_customer: Customer
    ) -> None:
        response = staff_client.get(reverse("bookings:customer_list"))
        assert response.status_code == 200
        assert b"Kowalski" in response.content

    def test_customer_create(self, staff_client, db) -> None:
        response = staff_client.post(
            reverse("bookings:customer_create"),
            {
                "first_name": "Anna",
                "last_name": "Nowak",
                "email": "anna@example.com",
                "phone": "",
                "company_name": "",
                "tax_id": "",
                "street": "",
                "city": "",
                "postal_code": "",
                "country": "PL",
                "notes": "",
            },
        )
        assert response.status_code == 302
        assert Customer.objects.filter(email="anna@example.com").exists()

    def test_customer_edit(self, staff_client, sample_customer: Customer) -> None:
        response = staff_client.post(
            reverse("bookings:customer_edit", kwargs={"pk": sample_customer.pk}),
            {
                "first_name": "Jan",
                "last_name": "Kowalski",
                "email": "jan@example.com",
                "phone": "+48999999999",
                "company_name": "Firma JK",
                "tax_id": "",
                "street": "",
                "city": "",
                "postal_code": "",
                "country": "PL",
                "notes": "",
            },
        )
        assert response.status_code == 302
        sample_customer.refresh_from_db()
        assert sample_customer.phone == "+48999999999"
        assert sample_customer.company_name == "Firma JK"

    def test_customer_delete(self, staff_client, sample_customer: Customer) -> None:
        pk = sample_customer.pk
        response = staff_client.post(
            reverse("bookings:customer_delete", kwargs={"pk": pk}),
        )
        assert response.status_code == 302
        assert not Customer.objects.filter(pk=pk).exists()

    def test_customer_search(self, staff_client, sample_customer: Customer) -> None:
        response = staff_client.get(
            reverse("bookings:customer_list"),
            {"q": "jan@example"},
        )
        assert response.status_code == 200
        assert b"Kowalski" in response.content
