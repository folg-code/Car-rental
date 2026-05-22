from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, PriceLine, PriceLineType, Reservation
from apps.fleet.models import Car, CarCategory, CarStatus


@pytest.mark.django_db
class TestPriceLine:
    def test_snapshot_line(self) -> None:
        cat = CarCategory.objects.create(name="SUV", slug="suv-pl")
        car = Car.objects.create(
            category=cat,
            registration_number="PL001",
            make="A",
            model="B",
            year=2022,
            status=CarStatus.ACTIVE,
        )
        customer = Customer.objects.create(
            first_name="Jan",
            last_name="Kowalski",
            email="jan@pl.example",
        )
        from datetime import UTC, datetime

        reservation = Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 7, 5, 10, 0, tzinfo=UTC),
        )
        line = PriceLine.objects.create(
            reservation=reservation,
            line_type=PriceLineType.DAILY_RENTAL,
            description="Wynajem 4 doby — Kompakt",
            quantity=Decimal("4"),
            unit_price=Decimal("120.00"),
            total_amount=Decimal("480.00"),
            source_code="daily_rate:suv",
        )
        assert line.pk is not None
        assert reservation.price_lines.count() == 1

    def test_total_must_match_quantity_times_unit(self) -> None:
        cat = CarCategory.objects.create(name="X", slug="x-pl")
        car = Car.objects.create(
            category=cat,
            registration_number="PL002",
            make="A",
            model="B",
            year=2022,
        )
        customer = Customer.objects.create(
            first_name="A",
            last_name="B",
            email="ab@example.com",
        )
        from datetime import UTC, datetime

        reservation = Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 8, 3, 10, 0, tzinfo=UTC),
        )
        line = PriceLine(
            reservation=reservation,
            line_type=PriceLineType.DAILY_RENTAL,
            description="Blad",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
            total_amount=Decimal("250.00"),
        )
        with pytest.raises(ValidationError):
            line.save()
