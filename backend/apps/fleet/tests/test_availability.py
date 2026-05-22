from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError

from apps.fleet.models import AvailabilityBlockType, Car, CarCategory, CarStatus
from apps.fleet.services.availability import AvailabilityService
from apps.fleet.services.maintenance import FleetMaintenanceService


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt")


@pytest.fixture
def car(db, category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="WW12345",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestAvailabilityService:
    def test_rejects_invalid_interval(self, car: Car) -> None:
        start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            AvailabilityService.is_car_available(car, start, end)

    def test_car_available_without_blocks(self, car: Car) -> None:
        start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
        assert AvailabilityService.is_car_available(car, start, end) is True

    def test_car_unavailable_when_blocked(self, car: Car) -> None:
        start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
        FleetMaintenanceService.create_availability_block(
            car_id=car.pk,
            start_at=datetime(2026, 6, 2, 0, 0, tzinfo=UTC),
            end_at=datetime(2026, 6, 4, 0, 0, tzinfo=UTC),
            reason="Serwis",
            block_type=AvailabilityBlockType.SERVICE,
        )
        assert AvailabilityService.is_car_available(car, start, end) is False

    def test_inactive_car_not_available(self, car: Car) -> None:
        car.status = CarStatus.INACTIVE
        car.save()
        start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
        assert AvailabilityService.is_car_available(car, start, end) is False


@pytest.mark.django_db
class TestOverlappingBlocks:
    def test_rejects_overlapping_block(self, car: Car) -> None:
        FleetMaintenanceService.create_availability_block(
            car_id=car.pk,
            start_at=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
            end_at=datetime(2026, 7, 5, 18, 0, tzinfo=UTC),
            reason="Serwis olejowy",
        )
        with pytest.raises(ValidationError):
            FleetMaintenanceService.create_availability_block(
                car_id=car.pk,
                start_at=datetime(2026, 7, 3, 10, 0, tzinfo=UTC),
                end_at=datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
                reason="Nakladajaca sie blokada",
            )

    def test_allows_adjacent_blocks(self, car: Car) -> None:
        FleetMaintenanceService.create_availability_block(
            car_id=car.pk,
            start_at=datetime(2026, 8, 1, 8, 0, tzinfo=UTC),
            end_at=datetime(2026, 8, 3, 18, 0, tzinfo=UTC),
            reason="Blok 1",
        )
        block2 = FleetMaintenanceService.create_availability_block(
            car_id=car.pk,
            start_at=datetime(2026, 8, 3, 18, 0, tzinfo=UTC),
            end_at=datetime(2026, 8, 5, 18, 0, tzinfo=UTC),
            reason="Blok 2",
        )
        assert block2.pk is not None
