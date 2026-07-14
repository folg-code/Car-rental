"""Testy emaili potwierdzenia rezerwacji."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core import mail

from apps.bookings.constants import (
    RESERVATION_EMAIL_CONFIRMED,
    RESERVATION_EMAIL_PENDING,
)
from apps.bookings.services.reservation import ReservationService
from apps.bookings.services.reservation_email import ReservationEmailService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.public_booking import PublicBookingOrchestrator


@pytest.fixture(autouse=True)
def locmem_email(settings) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@test.car-rental.local"
    settings.PUBLIC_SITE_BASE_URL = "http://testserver"
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-email")


@pytest.fixture
def car(db, category: CarCategory) -> Car:
    price_list = PriceList.objects.create(
        name="Email tests",
        slug="email-tests",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100.00"),
    )
    return Car.objects.create(
        category=category,
        registration_number="MAIL01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestReservationEmailService:
    def test_send_pending_email(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 7, 5, 10, 0, tzinfo=UTC),
            first_name="Anna",
            last_name="Nowak",
            email="anna@mail.test",
        )
        mail.outbox.clear()

        sent = ReservationEmailService.send_reservation_email(
            result.reservation.pk,
            email_kind=RESERVATION_EMAIL_PENDING,
        )
        assert sent is True
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == ["anna@mail.test"]
        assert str(result.reservation.pk) in message.subject
        assert "Zaplac online" in message.alternatives[0][0]
        assert "/rezerwacja/" in message.body

    def test_send_confirmed_email_direct(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 8, 5, 10, 0, tzinfo=UTC),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@mail.test",
        )
        mail.outbox.clear()
        reservation = ReservationService.confirm(result.reservation)

        sent = ReservationEmailService.send_reservation_email(
            reservation.pk,
            email_kind=RESERVATION_EMAIL_CONFIRMED,
        )
        assert sent is True
        assert len(mail.outbox) == 1
        assert "potwierdzona" in mail.outbox[0].subject.lower()

    def test_skips_when_customer_has_no_email(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 9, 5, 10, 0, tzinfo=UTC),
            first_name="Ewa",
            last_name="Test",
            phone="+48111222333",
        )
        mail.outbox.clear()

        sent = ReservationEmailService.send_reservation_email(
            result.reservation.pk,
            email_kind=RESERVATION_EMAIL_PENDING,
        )
        assert sent is False
        assert len(mail.outbox) == 0


@pytest.mark.django_db(transaction=True)
class TestReservationEmailOnCommit:
    def test_submit_enqueues_pending_email(self, car: Car) -> None:
        PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
            first_name="Piotr",
            last_name="Mail",
            email="piotr@mail.test",
        )
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["piotr@mail.test"]
        assert "Oczekuje platnosci" in mail.outbox[0].body

    def test_confirm_enqueues_confirmed_email(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 11, 5, 10, 0, tzinfo=UTC),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@mail.test",
        )
        mail.outbox.clear()
        ReservationService.confirm(result.reservation)

        assert len(mail.outbox) == 1
        assert "potwierdzona" in mail.outbox[0].subject.lower()
