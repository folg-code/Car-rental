from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.bookings.models import Customer, Reservation, ReservationStatus
from apps.dashboard.selectors.metrics import get_dashboard_metrics
from apps.dashboard.services.metrics import DashboardMetricsService
from apps.fleet.models import AvailabilityBlockType, Car, CarCategory, CarStatus
from apps.fleet.services.maintenance import FleetMaintenanceService


@pytest.mark.django_db
class TestDashboardMetrics:
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
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(days=5),
            status=ReservationStatus.CONFIRMED,
        )

        metrics = get_dashboard_metrics(as_of=now)
        assert metrics.active_reservations == 1
        assert metrics.free_cars == 0
        assert metrics.upcoming_returns == 1

    def test_free_cars_excludes_maintenance_block(self) -> None:
        cat = CarCategory.objects.create(name="Test", slug="test-block")
        car = Car.objects.create(
            category=cat,
            registration_number="METRIC02",
            make="A",
            model="B",
            year=2020,
            status=CarStatus.ACTIVE,
        )
        now = timezone.now()
        FleetMaintenanceService.create_availability_block(
            car_id=car.pk,
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
            reason="Przeglad",
            block_type=AvailabilityBlockType.SERVICE,
        )

        metrics = get_dashboard_metrics(as_of=now)
        assert metrics.free_cars == 0

    def test_service_delegates_to_selector(self) -> None:
        metrics = DashboardMetricsService.get_home_metrics()
        assert metrics.active_reservations >= 0
        assert metrics.active_rentals >= 0
        assert metrics.free_cars >= 0
        assert metrics.upcoming_returns >= 0
        assert metrics.unpaid_rentals >= 0
        assert metrics.month_revenue >= Decimal("0")
        assert metrics.expiring_fleet_documents >= 0
