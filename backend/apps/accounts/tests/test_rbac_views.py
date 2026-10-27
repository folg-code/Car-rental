import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService


@pytest.fixture
def employee_client(client, db):
    UserService.create_user(
        username="rbac_employee",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="rbac_employee", password="secure-pass-123")
    return client


@pytest.fixture
def accountant_client(client, db):
    UserService.create_user(
        username="rbac_accountant",
        password="secure-pass-123",
        role=UserRole.ACCOUNTANT,
    )
    client.login(username="rbac_accountant", password="secure-pass-123")
    return client


@pytest.mark.django_db
class TestGranularRbac:
    def test_employee_cannot_open_pricing(self, employee_client) -> None:
        response = employee_client.get(reverse("pricing:price_list_list"))
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_employee_cannot_open_financial_report(self, employee_client) -> None:
        response = employee_client.get(reverse("dashboard:financial_report"))
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_accountant_can_open_financial_report(self, accountant_client) -> None:
        response = accountant_client.get(reverse("dashboard:financial_report"))
        assert response.status_code == 200

    def test_accountant_cannot_open_pricing(self, accountant_client) -> None:
        response = accountant_client.get(reverse("pricing:price_list_list"))
        assert response.status_code == 302
