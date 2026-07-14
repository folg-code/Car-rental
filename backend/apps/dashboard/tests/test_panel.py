from datetime import date, timedelta

import pytest
from django.conf import settings
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import RentalStatus
from apps.dashboard.views import DASHBOARD_QUEUE_LIMIT
from apps.fleet.models import Car, CarDocument, CarDocumentType, CarStatus

from .conftest import sample_document_file


@pytest.mark.django_db
class TestPanelAccess:
    def test_panel_redirects_anonymous_user(self, client) -> None:
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("accounts:login"))

    def test_panel_uses_internal_layout(self, client, staff_user) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))
        assert response.status_code == 200
        assert b"Panel operacyjny" in response.content
        assert b"Car Rental" in response.content
        assert b"Pulpit" in response.content
        assert b"Aktywne rezerwacje" in response.content

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
            "pending_handover",
            "pending_return",
        ):
            assert key in response.context

        assert len(response.context["unpaid_rentals_queue"]) <= DASHBOARD_QUEUE_LIMIT
        assert len(response.context["fleet_document_alerts"]) <= DASHBOARD_QUEUE_LIMIT
        assert len(response.context["pending_handover"]) <= DASHBOARD_QUEUE_LIMIT
        assert len(response.context["pending_return"]) <= DASHBOARD_QUEUE_LIMIT


@pytest.mark.django_db
class TestPanelDashboardWidgets:
    def test_panel_shows_extended_kpi_widgets(self, client, staff_user) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        content = response.content
        assert b"Nieoplacone wynajmy" in content
        assert b"Przychod (ten miesiac)" in content
        assert b"Alerty dokumentow floty" in content
        assert b"Kolejka operacji" in content
        assert b"Do wydania" in content
        assert b"Do zwrotu" in content

    def test_panel_shows_unpaid_rental_queue(
        self, client, staff_user, scheduled_rental
    ) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert f"Wynajem #{scheduled_rental.pk}".encode() in response.content
        assert b"Platnosc" in response.content

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

    def test_panel_shows_pending_handover_queue(
        self, client, staff_user, scheduled_rental
    ) -> None:
        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"Do wydania" in response.content
        assert f"Wynajem #{scheduled_rental.pk}".encode() in response.content
        assert b"Wydaj" in response.content

    def test_panel_shows_pending_return_queue(
        self, client, staff_user, scheduled_rental
    ) -> None:
        scheduled_rental.status = RentalStatus.ACTIVE
        scheduled_rental.save(update_fields=["status"])

        client.login(username="dashboard-staff", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"Do zwrotu" in response.content
        assert f"Wynajem #{scheduled_rental.pk}".encode() in response.content
        assert b"Zwrot" in response.content


@pytest.mark.django_db
class TestLocaleAndMediaSettings:
    def test_polish_locale_configured(self) -> None:
        assert settings.LANGUAGE_CODE == "pl"
        assert settings.TIME_ZONE == "Europe/Warsaw"

    def test_media_and_static_roots_configured(self) -> None:
        assert settings.MEDIA_ROOT is not None
        assert settings.MEDIA_URL == "/media/"
        assert settings.STATIC_ROOT is not None
