import base64
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.models import Document, DocumentType
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.operations.services.handover import HandoverService
from apps.pricing.models import DailyRate, PriceList

# 1x1 px PNG — poprawny obraz dla WeasyPrint w CI (nie sam naglowek PNG).
MINIMAL_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AAwMCAO+"
    "X9qfAAAAABJRU5ErkJggg=="
)


def tiny_signature_image(name: str = "sig.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        MINIMAL_PNG_BYTES,
        content_type="image/png",
    )


@pytest.fixture(autouse=True)
def locmem_email(settings) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@test.car-rental.local"


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV", slug="suv-docs", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Documents tests",
        slug="docs-tests",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("100"))
    return pl


@pytest.fixture
def scheduled_rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Anna",
        last_name="Nowak",
        email="anna@docs.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1DOC01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
    )
    start = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)
    end = datetime(2026, 8, 14, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)


@pytest.fixture
def handover_document(scheduled_rental) -> Document:
    HandoverService.complete_handover(
        scheduled_rental.pk,
        mileage=10_200,
        fuel_level_percent=90,
        signer_name="Anna Nowak",
        signature_image=tiny_signature_image(),
    )
    return Document.objects.get(
        handover_protocol__rental=scheduled_rental,
        document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
        version=1,
    )
