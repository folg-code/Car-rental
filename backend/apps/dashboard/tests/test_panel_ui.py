from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarDocument, CarDocumentType, CarStatus
from apps.pricing.models import DailyRate, PriceList


def _sample_file() -> SimpleUploadedFile:
    return SimpleUploadedFile(
        "doc.pdf", b"%PDF-1.4 test", content_type="application/pdf"
    )


@pytest.fixture
def staff_user(db):
    return UserService.create_user(
        username="panel-ui",
        password="secure-pass-123",
        role=UserRole.MANAGER,
    )


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-panel-ui",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik panel UI",
        slug="test-panel-ui",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("200.00"),
    )
    return price_list


@pytest.mark.django_db
class TestPanelDashboardUI:
    def test_panel_shows_extended_kpi_widgets(self, client, staff_user) -> None:
        client.login(username="panel-ui", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        content = response.content
        assert b"Aktywne rezerwacje" in content
        assert b"Nieoplacone wynajmy" in content
        assert b"Przychod (ten miesiac)" in content
        assert b"Alerty dokumentow floty" in content
        assert b"Kolejka operacji" in content

    def test_panel_shows_unpaid_rental_queue(
        self, client, staff_user, category
    ) -> None:
        customer = Customer.objects.create(
            first_name="Anna",
            last_name="Nowak",
            email="anna@panel.test",
        )
        car = Car.objects.create(
            category=category,
            registration_number="PANEL01",
            make="Toyota",
            model="Yaris",
            year=2022,
            status=CarStatus.ACTIVE,
        )
        start = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 7, 5, 10, 0, tzinfo=UTC)
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        rental = RentalService.convert_from_reservation(reservation)

        client.login(username="panel-ui", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert f"Wynajem #{rental.pk}".encode() in response.content
        assert b"Platnosc" in response.content

    def test_panel_shows_fleet_document_alert(
        self, client, staff_user, category
    ) -> None:
        car = Car.objects.create(
            category=category,
            registration_number="PANEL02",
            make="Toyota",
            model="Yaris",
            year=2022,
            status=CarStatus.ACTIVE,
        )
        CarDocument.objects.create(
            car=car,
            document_type=CarDocumentType.INSURANCE,
            file=_sample_file(),
            valid_until=date.today() + timedelta(days=10),
        )

        client.login(username="panel-ui", password="secure-pass-123")
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"PANEL02" in response.content
        assert b"Ubezpieczenie OC/AC" in response.content
