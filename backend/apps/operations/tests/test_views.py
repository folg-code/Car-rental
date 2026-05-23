import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="ops_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="ops_staff", password="secure-pass-123")
    return client


@pytest.mark.django_db
class TestOperationsViews:
    def test_home_requires_login(self, client) -> None:
        assert client.get(reverse("operations:home")).status_code == 302

    def test_home_for_staff(self, staff_client, scheduled_rental) -> None:
        response = staff_client.get(reverse("operations:home"))
        assert response.status_code == 200
        assert b"Operacje w terenie" in response.content

    def test_handover_form(self, staff_client, scheduled_rental) -> None:
        response = staff_client.get(
            reverse(
                "operations:handover_create",
                kwargs={"rental_id": scheduled_rental.pk},
            )
        )
        assert response.status_code == 200
        assert b"Protokol wydania" in response.content
