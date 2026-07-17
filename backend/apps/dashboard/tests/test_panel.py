from datetime import date, timedelta

import pytest
from django.conf import settings
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.dashboard.views import DASHBOARD_QUEUE_LIMIT
from apps.fleet.models import Car, CarDocument, CarDocumentType, CarStatus

from .conftest import sample_document_file


@pytest.mark.django_db
class TestPanelAccess:
    def test_entry_redirects_anonymous_user(self, client) -> None:
        response = client.get(reverse("dashboard:entry"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("accounts:login"))

    def test_panel_redirects_anonymous_user(self, client) -> None:
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("accounts:login"))

    def test_entry_shows_mode_tiles(self, client, staff_user) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:entry"))
        assert response.status_code == 200
        assert b"Panel administratora" in response.content
        assert "Wydaj / zwróć pojazd".encode() in response.content
        assert reverse("dashboard:home").encode() in response.content
        assert reverse("operations:home").encode() in response.content

    def test_admin_panel_uses_internal_layout(self, client, staff_user) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
        assert b"Pulpit" in response.content
        assert b"Car Rental" in response.content
        assert b"Aktywne rezerwacje" in response.content
        assert "Zmień tryb pracy".encode() in response.content

    def test_admin_nav_excludes_operations(self, client, staff_user) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))
        nav_html = response.content.decode()
        # Sidebar labels — "Operacje" as nav item removed (Sprint 12.7).
        assert (
            'href="' + reverse("operations:home") + '"'
            not in nav_html.split("<main")[0]
        )
        assert "Flota" in nav_html

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
class TestPanelHomeContext:
    def test_panel_exposes_dashboard_context(self, client, staff_user) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        for key in (
            "metrics",
            "today",
            "unpaid_rentals_queue",
            "fleet_document_alerts",
        ):
            assert key in response.context

        assert "pending_handover" not in response.context
        assert "pending_return" not in response.context
        assert len(response.context["unpaid_rentals_queue"]) <= DASHBOARD_QUEUE_LIMIT
        assert len(response.context["fleet_document_alerts"]) <= DASHBOARD_QUEUE_LIMIT


@pytest.mark.django_db
class TestPanelDashboardWidgets:
    def test_panel_shows_extended_kpi_widgets(self, client, staff_user) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        content = response.content
        assert "Nieopłacone wynajmy".encode() in content
        assert "Przychód (ten miesiąc)".encode() in content
        assert "Alerty dokumentów floty".encode() in content
        assert b"Kolejka operacji" not in content
        assert b"Do wydania" not in content
        assert b"Do zwrotu" not in content

    def test_panel_shows_unpaid_rental_queue(
        self, client, staff_user, scheduled_rental
    ) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert f"Wynajem #{scheduled_rental.pk}".encode() in response.content
        assert "Płatność".encode() in response.content

    def test_panel_shows_fleet_document_alert(
        self, client, staff_user, category
    ) -> None:
        car = Car.objects.create(
            category=category,
            registration_number="DASH02",
            make="Toyota",
            model="Yaris",
            year=2022,
            status=CarStatus.ACTIVE,
        )
        CarDocument.objects.create(
            car=car,
            document_type=CarDocumentType.INSURANCE,
            file=sample_document_file(),
            valid_until=date.today() + timedelta(days=10),
        )

        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"DASH02" in response.content
        assert b"Ubezpieczenie OC/AC" in response.content


@pytest.mark.django_db
class TestLocaleAndMediaSettings:
    def test_polish_locale_configured(self) -> None:
        assert settings.LANGUAGE_CODE == "pl"
        assert settings.TIME_ZONE == "Europe/Warsaw"

    def test_media_and_static_roots_configured(self) -> None:
        assert settings.MEDIA_ROOT is not None
        assert settings.MEDIA_URL == "/media/"
        assert settings.STATIC_ROOT is not None
