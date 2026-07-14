from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.operations.services.surcharge_preview import (
    EXTRA_KM_CODE,
    FUEL_REFILL_CODE,
    SurchargePreviewService,
)
from apps.pricing.models import ExtraService, ExtraServiceChargeType, PriceList


@pytest.fixture
def surcharge_price_list(db) -> PriceList:
    PriceList.objects.all().delete()
    pl = PriceList.objects.create(
        name="Surcharge test",
        slug="surcharge-test",
        is_default=True,
        is_active=True,
    )
    ExtraService.objects.create(
        price_list=pl,
        code=FUEL_REFILL_CODE,
        name="Uzupelnienie paliwa",
        charge_type=ExtraServiceChargeType.PER_UNIT,
        amount=Decimal("5.00"),
    )
    ExtraService.objects.create(
        price_list=pl,
        code=EXTRA_KM_CODE,
        name="Dodatkowy km",
        charge_type=ExtraServiceChargeType.PER_UNIT,
        amount=Decimal("1.50"),
    )
    return pl


@pytest.mark.django_db
class TestSurchargePreviewService:
    def test_preview_calculates_fuel_and_km(
        self, surcharge_price_list: PriceList
    ) -> None:
        preview = SurchargePreviewService.preview(
            handover_mileage=10_000,
            handover_fuel=100,
            return_mileage=10_350,
            return_fuel=70,
            on_date=datetime(2026, 8, 5, 10, 0, tzinfo=UTC).date(),
        )
        assert len(preview.lines) == 2
        fuel_line = next(
            line for line in preview.lines if line.code == FUEL_REFILL_CODE
        )
        km_line = next(line for line in preview.lines if line.code == EXTRA_KM_CODE)
        assert fuel_line.total == Decimal("150.00")
        assert km_line.total == Decimal("525.00")
        assert preview.total == Decimal("675.00")
        assert "paliwa" in preview.summary_notes.lower()
        assert "350" in preview.summary_notes

    def test_preview_no_surcharges_when_unchanged(
        self, surcharge_price_list: PriceList
    ) -> None:
        preview = SurchargePreviewService.preview(
            handover_mileage=10_000,
            handover_fuel=80,
            return_mileage=10_000,
            return_fuel=80,
        )
        assert preview.lines == ()
        assert preview.total == Decimal("0")
        assert preview.summary_notes == ""

    def test_preview_without_price_list_uses_text_only(self, db) -> None:
        PriceList.objects.all().delete()
        preview = SurchargePreviewService.preview(
            handover_mileage=10_000,
            handover_fuel=100,
            return_mileage=10_200,
            return_fuel=80,
        )
        assert preview.lines == ()
        assert "paliwa" in preview.summary_notes.lower()
        assert "200" in preview.summary_notes
