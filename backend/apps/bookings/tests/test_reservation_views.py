from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import (
    Customer,
    Reservation,
    ReservationPricingMode,
    ReservationStatus,
)
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="res_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="res_staff", password="secure-pass-123")
    return client


@pytest.fixture
def car(db) -> Car:
    cat = CarCategory.objects.create(name="Kompakt", slug="kompakt-res")
    return Car.objects.create(
        category=cat,
        registration_number="WWRES01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture(autouse=True)
def default_price_list(db, car: Car) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik testowy rezerwacji",
        slug="test-rezerwacje-widoki",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=car.category,
        amount=Decimal("120.00"),
    )
    return price_list


@pytest.fixture
def customer(db) -> Customer:
    return Customer.objects.create(
        first_name="Anna",
        last_name="Nowak",
        email="anna@example.com",
    )


@pytest.fixture
def sample_reservation(customer: Customer, car: Car) -> Reservation:
    return Reservation.objects.create(
        customer=customer,
        car=car,
        start_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        end_at=datetime(2026, 8, 5, 10, 0, tzinfo=UTC),
        status=ReservationStatus.DRAFT,
    )


@pytest.mark.django_db
class TestReservationViews:
    def test_list_requires_login(self, client) -> None:
        response = client.get(reverse("bookings:reservation_list"))
        assert response.status_code == 302

    def test_list_for_staff(
        self, staff_client, sample_reservation: Reservation
    ) -> None:
        response = staff_client.get(reverse("bookings:reservation_list"))
        assert response.status_code == 200
        assert (
            b"#1" in response.content
            or str(sample_reservation.pk).encode() in response.content
        )

    def test_create_reservation(
        self, staff_client, customer: Customer, car: Car
    ) -> None:
        response = staff_client.post(
            reverse("bookings:reservation_create"),
            {
                "customer": customer.pk,
                "car": car.pk,
                "start_at": "2026-09-01T10:00",
                "end_at": "2026-09-05T10:00",
                "status": ReservationStatus.DRAFT,
                "pricing_mode": ReservationPricingMode.AUTO,
                "notes": "Testowa rezerwacja",
            },
        )
        assert response.status_code == 302
        assert Reservation.objects.filter(notes="Testowa rezerwacja").exists()

    def test_confirm_reservation(
        self, staff_client, sample_reservation: Reservation
    ) -> None:
        response = staff_client.post(
            reverse(
                "bookings:reservation_confirm",
                kwargs={"pk": sample_reservation.pk},
            ),
        )
        assert response.status_code == 302
        sample_reservation.refresh_from_db()
        assert sample_reservation.status == ReservationStatus.CONFIRMED

    def test_cancel_reservation(
        self, staff_client, sample_reservation: Reservation
    ) -> None:
        sample_reservation.status = ReservationStatus.CONFIRMED
        sample_reservation.save()
        response = staff_client.post(
            reverse(
                "bookings:reservation_cancel",
                kwargs={"pk": sample_reservation.pk},
            ),
            {"reason": "Zmiana planow"},
        )
        assert response.status_code == 302
        sample_reservation.refresh_from_db()
        assert sample_reservation.status == ReservationStatus.CANCELLED

    def test_status_filter(self, staff_client, sample_reservation: Reservation) -> None:
        response = staff_client.get(
            reverse("bookings:reservation_list"),
            {"status": ReservationStatus.DRAFT},
        )
        assert response.status_code == 200
        assert sample_reservation.customer.last_name.encode() in response.content

    def test_expire_reservation(
        self, staff_client, sample_reservation: Reservation
    ) -> None:
        sample_reservation.status = ReservationStatus.PENDING_PAYMENT
        sample_reservation.save()
        response = staff_client.post(
            reverse(
                "bookings:reservation_expire",
                kwargs={"pk": sample_reservation.pk},
            ),
        )
        assert response.status_code == 302
        sample_reservation.refresh_from_db()
        assert sample_reservation.status == ReservationStatus.EXPIRED
