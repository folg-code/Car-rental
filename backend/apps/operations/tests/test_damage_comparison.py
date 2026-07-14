from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus, DamageStatus
from apps.fleet.services.damage import DamageService
from apps.operations.models import HandoverProtocol
from apps.operations.selectors.damage_comparison import get_return_damage_comparison
from apps.operations.services.damage_snapshot import DamageSnapshotService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Compact", slug="compact-dmg", deposit=Decimal("300")
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Damage compare",
        slug="damage-compare",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("80"))
    return pl


@pytest.fixture
def handover_with_snapshots(db, category: CarCategory) -> HandoverProtocol:
    customer = Customer.objects.create(
        first_name="Anna",
        last_name="Nowak",
        email="anna@damage.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1DMG01",
        make="VW",
        model="Golf",
        year=2021,
        status=CarStatus.ACTIVE,
        mileage=20_000,
    )
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
        end_at=datetime(2026, 9, 5, 10, 0, tzinfo=UTC),
        status=ReservationStatus.CONFIRMED,
    )
    rental = RentalService.convert_from_reservation(reservation)
    DamageService.report_damage(
        car=car,
        description="Rysa na zderzaku",
        location="przod",
        severity="minor",
    )
    handover = HandoverProtocol.objects.create(
        rental=rental,
        mileage=20_100,
        fuel_level_percent=90,
        completed_at=datetime(2026, 9, 1, 11, 0, tzinfo=UTC),
    )
    DamageSnapshotService.freeze_active_damages_for_handover(handover)
    return handover


@pytest.mark.django_db
class TestDamageComparison:
    def test_unchanged_damage(self, handover_with_snapshots: HandoverProtocol) -> None:
        rows = get_return_damage_comparison(handover_with_snapshots)
        assert len(rows) == 1
        assert rows[0].status == "unchanged"
        assert rows[0].handover_description == "Rysa na zderzaku"

    def test_new_damage_at_return(
        self, handover_with_snapshots: HandoverProtocol
    ) -> None:
        car = handover_with_snapshots.rental.reservation.car
        DamageService.report_damage(
            car=car,
            description="Peknieta szyba",
            location="tyl",
            severity="major",
        )
        rows = get_return_damage_comparison(handover_with_snapshots)
        statuses = {row.status for row in rows}
        assert "unchanged" in statuses
        assert "new_at_return" in statuses

    def test_resolved_damage(self, handover_with_snapshots: HandoverProtocol) -> None:
        car = handover_with_snapshots.rental.reservation.car
        damage = car.damages.first()
        damage.status = DamageStatus.REPAIRED
        damage.save(update_fields=["status"])
        rows = get_return_damage_comparison(handover_with_snapshots)
        assert len(rows) == 1
        assert rows[0].status == "resolved"
