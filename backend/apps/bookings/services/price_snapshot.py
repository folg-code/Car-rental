from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.bookings.models import (
    PriceLine,
    PriceLineType,
    Reservation,
    ReservationPricingMode,
    ReservationStatus,
)
from apps.fleet.models import Car
from apps.pricing.models import PriceList
from apps.pricing.services.pricing import PricingService

MUTABLE_FOR_PRICING = frozenset(
    {
        ReservationStatus.DRAFT,
        ReservationStatus.PENDING_PAYMENT,
    }
)


class PriceSnapshotService:
    @staticmethod
    def can_recalculate(reservation: Reservation) -> bool:
        return reservation.status in MUTABLE_FOR_PRICING

    @staticmethod
    def reservation_total(reservation: Reservation) -> Decimal:
        return sum(
            (line.total_amount for line in reservation.price_lines.all()),
            Decimal("0"),
        )

    @staticmethod
    def _freeze_custom(reservation: Reservation) -> list[PriceLine]:
        total = reservation.custom_total
        if total is None:
            raise ValidationError("Brak kwoty recznej do zapisania.")
        total = total.quantize(Decimal("0.01"))
        line = PriceLine.objects.create(
            reservation=reservation,
            line_type=PriceLineType.MANUAL,
            description="Kwota ustalona recznie",
            quantity=Decimal("1"),
            unit_price=total,
            total_amount=total,
            source_code="custom:manual",
            sort_order=0,
        )
        return [line]

    @staticmethod
    def _resolve_price_list(reservation: Reservation) -> PriceList | None:
        if reservation.pricing_mode == ReservationPricingMode.PRICE_LIST:
            return reservation.price_list
        if reservation.pricing_mode == ReservationPricingMode.AUTO:
            return None
        return None

    @staticmethod
    @transaction.atomic
    def freeze(
        reservation: Reservation,
        *,
        extra_codes: list[str] | None = None,
        replace: bool = True,
    ) -> list[PriceLine]:
        if reservation.status in (
            ReservationStatus.CANCELLED,
            ReservationStatus.EXPIRED,
            ReservationStatus.CONVERTED_TO_RENTAL,
        ):
            raise ValidationError(
                "Nie mozna naliczyc ceny dla rezerwacji w statusie koncowym."
            )

        if (
            reservation.status == ReservationStatus.CONFIRMED
            and reservation.price_lines.exists()
            and not replace
        ):
            raise ValidationError(
                "Potwierdzona rezerwacja ma juz zamrozony rozpis cen."
            )

        if (
            reservation.status == ReservationStatus.CONFIRMED
            and replace
            and reservation.price_lines.exists()
        ):
            raise ValidationError("Nie mozna przeliczyc ceny potwierdzonej rezerwacji.")

        if replace:
            reservation.price_lines.all().delete()

        if reservation.pricing_mode == ReservationPricingMode.CUSTOM:
            return PriceSnapshotService._freeze_custom(reservation)

        car = (
            Car.objects.select_related("category").filter(pk=reservation.car_id).first()
        )
        if car is None:
            raise ValidationError("Brak pojazdu przypisanego do rezerwacji.")

        result = PricingService.calculate(
            car=car,
            start_at=reservation.start_at,
            end_at=reservation.end_at,
            extra_codes=extra_codes,
            price_list=PriceSnapshotService._resolve_price_list(reservation),
        )

        created: list[PriceLine] = []
        for item in result.lines:
            line = PriceLine.objects.create(
                reservation=reservation,
                line_type=item.line_type,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_amount=item.total_amount,
                source_code=item.source_code,
                sort_order=item.sort_order,
            )
            created.append(line)
        return created
