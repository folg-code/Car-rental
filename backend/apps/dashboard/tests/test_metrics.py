from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.bookings.models import Customer, RentalStatus, Reservation, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.dashboard.selectors.metrics import get_dashboard_metrics
from apps.dashboard.services.metrics import DashboardMetricsService
from apps.fleet.models import (
    AvailabilityBlockType,
    Car,
    CarCategory,
    CarDocument,
    CarDocumentType,
    CarStatus,
)
from apps.fleet.services.maintenance import FleetMaintenanceService
from apps.payments.services.payment import PaymentService


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

    def test_active_rental_increments_kpi(self, category: CarCategory) -> None:
        customer = Customer.objects.create(
            first_name="R",
            last_name="Ental",
            email="rental@metrics.test",
        )
        car = Car.objects.create(
            category=category,
            registration_number="METRIC03",
            make="A",
            model="B",
            year=2020,
            status=CarStatus.ACTIVE,
        )
        as_of = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 7, 8, 10, 0, tzinfo=UTC),
            status=ReservationStatus.CONFIRMED,
        )
        RentalService.convert_from_reservation(reservation)

        metrics = get_dashboard_metrics(as_of=as_of)
        assert metrics.active_rentals == 1
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

    def test_extended_kpi_aggregation(self, scheduled_rental) -> None:
        as_of = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
        car = scheduled_rental.reservation.car
        CarDocument.objects.create(
            car=car,
            document_type=CarDocumentType.INSPECTION,
            file=SimpleUploadedFile(
                "doc.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            valid_until=date.today() + timedelta(days=14),
        )
        PaymentService.record_rental_fee(
            rental_id=scheduled_rental.pk,
            amount=Decimal("400.00"),
            paid_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        )
        scheduled_rental.status = RentalStatus.ACTIVE
        scheduled_rental.save(update_fields=["status"])

        metrics = get_dashboard_metrics(as_of=as_of)

        assert metrics.active_rentals == 1
        assert metrics.unpaid_rentals == 1
        assert metrics.month_revenue == Decimal("400.00")
        assert metrics.expiring_fleet_documents == 1

    def test_service_delegates_to_selector(self) -> None:
        metrics = DashboardMetricsService.get_home_metrics()
        assert metrics.active_reservations >= 0
        assert metrics.active_rentals >= 0
        assert metrics.free_cars >= 0
        assert metrics.upcoming_returns >= 0
        assert metrics.unpaid_rentals >= 0
        assert metrics.month_revenue >= Decimal("0")
        assert metrics.expiring_fleet_documents >= 0
