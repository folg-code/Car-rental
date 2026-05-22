from datetime import datetime

from django.core.exceptions import ValidationError

from apps.fleet.models import Car, CarStatus
from apps.fleet.selectors.availability import (
    get_booking_busy_intervals,
    get_overlapping_blocks,
)


class AvailabilityService:
    @staticmethod
    def validate_interval(start_at: datetime, end_at: datetime) -> None:
        if start_at >= end_at:
            raise ValidationError(
                "Data zakonczenia musi byc pozniejsza niz data rozpoczecia."
            )

    @staticmethod
    def has_overlapping_block(
        car_id: int,
        start_at: datetime,
        end_at: datetime,
        *,
        exclude_block_id: int | None = None,
    ) -> bool:
        AvailabilityService.validate_interval(start_at, end_at)
        return get_overlapping_blocks(
            car_id,
            start_at,
            end_at,
            exclude_block_id=exclude_block_id,
        ).exists()

    @staticmethod
    def assert_no_overlapping_block(
        car_id: int,
        start_at: datetime,
        end_at: datetime,
        *,
        exclude_block_id: int | None = None,
    ) -> None:
        if AvailabilityService.has_overlapping_block(
            car_id,
            start_at,
            end_at,
            exclude_block_id=exclude_block_id,
        ):
            raise ValidationError(
                "W tym przedziale istnieje juz blokada dostepnosci dla tego pojazdu."
            )

    @staticmethod
    def is_car_available(
        car: Car,
        start_at: datetime,
        end_at: datetime,
        *,
        exclude_block_id: int | None = None,
        exclude_reservation_id: int | None = None,
    ) -> bool:
        """
        Dostepnosc wyliczana — brak pola is_available na Car.

        Uwzglednia: status auta, blokady, (przyszle) rezerwacje z bookings.
        """
        AvailabilityService.validate_interval(start_at, end_at)

        if car.status != CarStatus.ACTIVE:
            return False

        if AvailabilityService.has_overlapping_block(
            car.pk,
            start_at,
            end_at,
            exclude_block_id=exclude_block_id,
        ):
            return False

        for busy_start, busy_end in get_booking_busy_intervals(
            car.pk,
            start_at,
            end_at,
            exclude_reservation_id=exclude_reservation_id,
        ):
            if busy_start < end_at and busy_end > start_at:
                return False

        return True
