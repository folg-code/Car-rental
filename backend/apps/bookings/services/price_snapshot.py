from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.bookings.models import PriceLine, Reservation, ReservationStatus
from apps.fleet.models import Car
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
        )

        if replace:
            reservation.price_lines.all().delete()

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
