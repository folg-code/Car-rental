from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus


def sample_document_file(name: str = "doc.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        b"%PDF-1.4 test",
        content_type="application/pdf",
    )


@pytest.fixture(autouse=True)
def locmem_email(settings) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@test.car-rental.local"


@pytest.fixture
def staff_user(db):
    return UserService.create_user(
        username="dashboard-staff",
        password="secure-pass-123",
        role=UserRole.MANAGER,
    )


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-dashboard-tests",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory):
    from apps.pricing.models import DailyRate, PriceList

    price_list = PriceList.objects.create(
        name="Cennik dashboard tests",
        slug="test-dashboard",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("200.00"),
    )
    return price_list


@pytest.fixture
def scheduled_rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@dashboard.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="DASH01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
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
    return RentalService.convert_from_reservation(reservation)
