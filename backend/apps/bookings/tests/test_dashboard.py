from datetime import timedelta

import pytest
from django.utils import timezone

from apps.bookings.models import Customer, Reservation, ReservationStatus
from apps.bookings.selectors.dashboard import get_bookings_dashboard_metrics
from apps.fleet.models import Car, CarCategory, CarStatus


@pytest.mark.django_db
class TestBookingsDashboardMetrics:
    def test_metrics_with_confirmed_reservation(self) -> None:
        cat = CarCategory.objects.create(name="Test", slug="test-dash")
        car = Car.objects.create(
            category=cat,
            registration_number="METRIC01",
            make="A",
            model="B",
            year=2020,
            status=CarStatus.ACTIVE,
        )
        customer = Customer.objects.create(
            first_name="T",
            last_name="U",
            email="tu@example.com",
        )
        now = timezone.now()
        Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=now,
            end_at=now + timedelta(days=5),
            status=ReservationStatus.CONFIRMED,
        )

        metrics = get_bookings_dashboard_metrics()
        assert metrics["active_reservations"] == 1
        assert metrics["free_cars"] == 0
        assert metrics["upcoming_returns"] == 1
