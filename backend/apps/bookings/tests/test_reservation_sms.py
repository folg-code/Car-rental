"""Testy SMS potwierdzenia rezerwacji."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.bookings.constants import (
    RESERVATION_EMAIL_CONFIRMED,
    RESERVATION_EMAIL_PENDING,
)
from apps.bookings.services.reservation import ReservationService
from apps.bookings.services.reservation_sms import ReservationSmsService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.notifications.models import SmsLog, SmsStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.public_booking import PublicBookingOrchestrator


@pytest.fixture(autouse=True)
def sms_settings(settings) -> None:
    settings.SMS_ENABLED = True
    settings.SMS_PROVIDER = "mock"
    settings.SMS_FROM_NUMBER = "+48111111111"
    settings.PUBLIC_SITE_BASE_URL = "http://testserver"
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-sms")


@pytest.fixture
def car(db, category: CarCategory) -> Car:
    price_list = PriceList.objects.create(
        name="SMS tests",
        slug="sms-tests",
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
        registration_number="SMS01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestReservationSmsService:
    def test_send_pending_sms(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 7, 5, 10, 0, tzinfo=UTC),
            first_name="Anna",
            last_name="Nowak",
            phone="+48111222333",
        )
        SmsLog.objects.all().delete()

        sent = ReservationSmsService.send_reservation_sms(
            result.reservation.pk,
            sms_kind=RESERVATION_EMAIL_PENDING,
        )
        assert sent is True
        log = SmsLog.objects.get()
        assert log.status == SmsStatus.SENT
        assert log.recipient_phone == "+48111222333"
        assert str(result.reservation.pk) in log.body
        assert "Zaplat online" in log.body

    def test_send_confirmed_sms(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 8, 5, 10, 0, tzinfo=UTC),
            first_name="Jan",
            last_name="Kowalski",
            phone="+48123456789",
        )
        SmsLog.objects.all().delete()
        reservation = ReservationService.confirm(result.reservation)

        sent = ReservationSmsService.send_reservation_sms(
            reservation.pk,
            sms_kind=RESERVATION_EMAIL_CONFIRMED,
        )
        assert sent is True
        log = SmsLog.objects.get()
        assert log.status == SmsStatus.SENT
        assert "potwierdzona" in log.body

    def test_skips_when_customer_has_no_phone(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 9, 5, 10, 0, tzinfo=UTC),
            first_name="Ewa",
            last_name="Test",
            email="ewa@mail.test",
        )
        SmsLog.objects.all().delete()

        sent = ReservationSmsService.send_reservation_sms(
            result.reservation.pk,
            sms_kind=RESERVATION_EMAIL_PENDING,
        )
        assert sent is False
        assert SmsLog.objects.count() == 0


@pytest.mark.django_db(transaction=True)
class TestReservationSmsOnCommit:
    def test_submit_enqueues_pending_sms(self, car: Car) -> None:
        PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
            first_name="Piotr",
            last_name="Sms",
            phone="+48987654321",
        )
        log = SmsLog.objects.get()
        assert log.status == SmsStatus.SENT
        assert log.recipient_phone == "+48987654321"
        assert "oczekuje platnosci" in log.body

    def test_confirm_enqueues_confirmed_sms(self, car: Car) -> None:
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 11, 5, 10, 0, tzinfo=UTC),
            first_name="Jan",
            last_name="Kowalski",
            phone="+48111222333",
        )
        SmsLog.objects.all().delete()
        ReservationService.confirm(result.reservation)

        log = SmsLog.objects.get()
        assert log.status == SmsStatus.SENT
        assert "potwierdzona" in log.body

    def test_sms_disabled_creates_skipped_log(self, car: Car, settings) -> None:
        settings.SMS_ENABLED = False
        PublicBookingOrchestrator.submit(
            car=car,
            start_at=datetime(2026, 12, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 12, 5, 10, 0, tzinfo=UTC),
            first_name="Off",
            last_name="Sms",
            phone="+48111222333",
        )
        log = SmsLog.objects.get()
        assert log.status == SmsStatus.SKIPPED
