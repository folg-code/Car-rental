from decimal import Decimal

import pytest
from django.db.models import Sum

from apps.payments.models import PaymentType, RentalCharge
from apps.payments.services.rental_charge import AccruedChargeLine, RentalChargeService


@pytest.mark.django_db
class TestRentalChargeService:
    def test_accrue_return_surcharges_is_idempotent(self, rental) -> None:
        lines = (
            AccruedChargeLine(
                source_code="fuel_refill",
                description="Uzupelnienie paliwa",
                amount=Decimal("150.00"),
            ),
            AccruedChargeLine(
                source_code="extra_km",
                description="Dodatkowy km",
                amount=Decimal("75.00"),
            ),
        )

        first = RentalChargeService.accrue_return_surcharges(
            rental_id=rental.pk,
            return_protocol_id=None,
            lines=lines,
        )
        second = RentalChargeService.accrue_return_surcharges(
            rental_id=rental.pk,
            return_protocol_id=None,
            lines=lines,
        )

        assert len(first) == 2
        assert second == []
        total = RentalCharge.objects.filter(rental_id=rental.pk).aggregate(
            total=Sum("amount")
        )["total"]
        assert total == Decimal("225.00")
        assert (
            RentalCharge.objects.filter(
                rental_id=rental.pk,
                payment_type=PaymentType.EXTRA_CHARGE,
            ).count()
            == 2
        )

    def test_skips_non_positive_amounts(self, rental) -> None:
        created = RentalChargeService.accrue_return_surcharges(
            rental_id=rental.pk,
            return_protocol_id=7,
            lines=(
                AccruedChargeLine(
                    source_code="extra_km",
                    description="Brak doplaty",
                    amount=Decimal("0.00"),
                ),
            ),
        )
        assert created == []
        assert RentalCharge.objects.filter(rental_id=rental.pk).count() == 0
