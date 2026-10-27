import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService


@pytest.mark.django_db
class TestUserService:
    def test_create_staff_user_sets_role_and_staff_flag(self) -> None:
        user = UserService.create_user(
            username="manager1",
            password="secure-pass-123",
            role=UserRole.MANAGER,
        )
        assert user.role == UserRole.MANAGER
        assert user.is_staff is True

    def test_change_role_updates_staff_flag(self) -> None:
        user = UserService.create_user(
            username="worker1",
            password="secure-pass-123",
            role=UserRole.EMPLOYEE,
        )
        UserService.change_role(user, UserRole.OWNER)
        user.refresh_from_db()
        assert user.role == UserRole.OWNER
        assert user.is_staff is True

    def test_deactivate_disables_user(self) -> None:
        user = UserService.create_user(
            username="worker2",
            password="secure-pass-123",
            role=UserRole.EMPLOYEE,
        )
        UserService.deactivate(user)
        user.refresh_from_db()
        assert user.is_active is False


@pytest.mark.django_db
class TestAuthViews:
    def test_staff_login_redirects_to_panel(self, client) -> None:
        UserService.create_user(
            username="emp",
            password="secure-pass-123",
            role=UserRole.EMPLOYEE,
        )
        response = client.post(
            reverse("accounts:login"),
            {"username": "emp", "password": "secure-pass-123"},
        )
        assert response.status_code == 302
        assert response.url == reverse("dashboard:entry")

    def test_customer_login_redirects_to_home(self, client) -> None:
        UserService.create_user(
            username="client1",
            password="secure-pass-123",
            role=UserRole.CUSTOMER,
        )
        response = client.post(
            reverse("accounts:login"),
            {"username": "client1", "password": "secure-pass-123"},
        )
        assert response.status_code == 302
        assert response.url == reverse("customer_portal:home")

    def test_anonymous_panel_redirects_to_login(self, client) -> None:
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("accounts:login"))

    def test_staff_can_access_panel(self, client) -> None:
        UserService.create_user(
            username="owner1",
            password="secure-pass-123",
            role=UserRole.OWNER,
        )
        client.login(username="owner1", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
        assert b"Pulpit" in response.content
