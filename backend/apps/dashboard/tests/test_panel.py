import pytest
from django.conf import settings
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService


@pytest.mark.django_db
class TestPanelLayout:
    def test_panel_uses_internal_layout(self, client) -> None:
        UserService.create_user(
            username="staff1",
            password="secure-pass-123",
            role=UserRole.MANAGER,
        )
        client.login(username="staff1", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
        assert b"Panel operacyjny" in response.content
        assert b"Car Rental" in response.content
        assert b"Pulpit" in response.content

    def test_fleet_list_accessible_for_staff(self, client) -> None:
        UserService.create_user(
            username="staff2",
            password="secure-pass-123",
            role=UserRole.EMPLOYEE,
        )
        client.login(username="staff2", password="secure-pass-123")
        response = client.get(reverse("fleet:car_list"))
        assert response.status_code == 200
        assert b"Flota" in response.content


@pytest.mark.django_db
class TestLocaleAndMediaSettings:
    def test_polish_locale_configured(self) -> None:
        assert settings.LANGUAGE_CODE == "pl"
        assert settings.TIME_ZONE == "Europe/Warsaw"

    def test_media_and_static_roots_configured(self) -> None:
        assert settings.MEDIA_ROOT is not None
        assert settings.MEDIA_URL == "/media/"
        assert settings.STATIC_ROOT is not None
