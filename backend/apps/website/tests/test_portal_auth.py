"""Testy logowania OTP do portalu klienta (Sprint 12.2)."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.customer import CustomerService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.portal_auth import (
    SESSION_CHALLENGE_KEY,
    PortalLoginService,
)


@pytest.fixture(autouse=True)
def _clear_cache_and_email(settings) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.DEFAULT_FROM_EMAIL = "noreply@test.car-rental.local"
    cache.clear()
    mail.outbox.clear()


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-portal-otp",
        deposit=Decimal("500"),
    )


@pytest.fixture(autouse=True)
def price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Portal OTP",
        slug="portal-otp",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("100"))
    return pl


@pytest.fixture
def customer(db) -> Customer:
    return CustomerService.create(
        first_name="Anna",
        last_name="Portal",
        email="anna-portal@test.pl",
        phone="+48111111111",
    )


@pytest.fixture
def reservation(db, customer: Customer, category: CarCategory):
    car = Car.objects.create(
        category=category,
        registration_number="OTP001",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )
    return ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
        end_at=datetime(2026, 9, 5, 10, 0, tzinfo=UTC),
        status=ReservationStatus.CONFIRMED,
    )


@pytest.mark.django_db
class TestPortalLoginService:
    def test_request_and_verify_by_email(self, customer: Customer) -> None:
        sent_code: dict[str, str] = {}

        def _send(*, customer_id: int, code: str) -> bool:
            sent_code["code"] = code
            return PortalLoginService.send_login_code_email(
                customer_id=customer_id,
                code=code,
            )

        with patch.object(
            PortalLoginService,
            "enqueue_login_code_email",
            side_effect=lambda **kwargs: _send(**kwargs),
        ):
            _customer, challenge = PortalLoginService.request_code(
                identifier=customer.email,
                client_ip="127.0.0.1",
            )

        assert sent_code["code"]
        assert len(mail.outbox) == 1
        user = PortalLoginService.verify_code(
            challenge=challenge,
            code=sent_code["code"],
        )
        customer.refresh_from_db()
        assert customer.user_id == user.pk
        assert user.role == UserRole.CUSTOMER
        assert not user.has_usable_password()

    def test_request_by_reservation_number(
        self, customer: Customer, reservation
    ) -> None:
        sent_code: dict[str, str] = {}

        def _send(*, customer_id: int, code: str) -> bool:
            sent_code["code"] = code
            return True

        with patch.object(
            PortalLoginService,
            "enqueue_login_code_email",
            side_effect=lambda **kwargs: _send(**kwargs),
        ):
            _customer, challenge = PortalLoginService.request_code(
                identifier=str(reservation.pk),
                client_ip="127.0.0.1",
            )

        user = PortalLoginService.verify_code(
            challenge=challenge,
            code=sent_code["code"],
        )
        assert user.email == customer.email

    def test_wrong_code_rejected(self, customer: Customer) -> None:
        with patch.object(PortalLoginService, "enqueue_login_code_email"):
            _customer, challenge = PortalLoginService.request_code(
                identifier=customer.email,
                client_ip="127.0.0.1",
            )
        with pytest.raises(ValidationError, match="Nieprawidlowy kod"):
            PortalLoginService.verify_code(challenge=challenge, code="000000")

    def test_rate_limit(self, customer: Customer) -> None:
        with patch.object(PortalLoginService, "enqueue_login_code_email"):
            for _ in range(5):
                PortalLoginService.request_code(
                    identifier=customer.email,
                    client_ip="10.0.0.9",
                )
            with pytest.raises(ValidationError, match="limit"):
                PortalLoginService.request_code(
                    identifier=customer.email,
                    client_ip="10.0.0.9",
                )


@pytest.mark.django_db
class TestPortalLoginViews:
    def test_otp_flow_logs_in(self, client, customer: Customer) -> None:
        sent_code: dict[str, str] = {}

        def _send(*, customer_id: int, code: str) -> bool:
            sent_code["code"] = code
            return True

        with patch.object(
            PortalLoginService,
            "enqueue_login_code_email",
            side_effect=lambda **kwargs: _send(**kwargs),
        ):
            response = client.post(
                reverse("customer_portal:otp_request"),
                {"identifier": customer.email},
            )
        assert response.status_code == 302
        assert response.url == reverse("customer_portal:otp_verify")
        assert client.session.get(SESSION_CHALLENGE_KEY)

        response = client.post(
            reverse("customer_portal:otp_verify"),
            {"code": sent_code["code"]},
        )
        assert response.status_code == 302
        assert response.url == reverse("customer_portal:home")

        home = client.get(reverse("customer_portal:home"))
        assert home.status_code == 200
        assert b"Anna" in home.content
