from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import (
    Rental,
    RentalStatus,
    Reservation,
    ReservationStatus,
)
from apps.bookings.selectors.availability import (
    get_overlapping_rentals,
    get_overlapping_reservations,
)
from apps.fleet.services.availability import AvailabilityService


class RentalService:
    @staticmethod
    def _assert_can_mutate(rental: Rental) -> None:
        if rental.is_terminal:
            msg = "Wynajem w statusie koncowym nie moze byc zmieniany."
            raise ValidationError(msg)

    @staticmethod
    def _assert_no_conflicting_rental(
        *,
        car_id: int,
        start_at: datetime,
        end_at: datetime,
        exclude_rental_id: int | None = None,
    ) -> None:
        if get_overlapping_rentals(
            car_id,
            start_at,
            end_at,
            exclude_rental_id=exclude_rental_id,
        ).exists():
            raise ValidationError(
                "W tym przedziale istnieje juz wynajem dla tego pojazdu."
            )

    @staticmethod
    @transaction.atomic
    def convert_from_reservation(
        reservation: Reservation,
        *,
        created_by_id: int | None = None,
        notes: str = "",
    ) -> Rental:
        if Rental.objects.filter(reservation_id=reservation.pk).exists():
            raise ValidationError("Ta rezerwacja ma juz przypisany wynajem.")
        if reservation.status != ReservationStatus.CONFIRMED:
            raise ValidationError(
                "Wynajem mozna utworzyc tylko z potwierdzonej rezerwacji."
            )
        if not reservation.price_lines.exists():
            raise ValidationError(
                "Brak snapshotu ceny — nalicz cene przed utworzeniem wynajmu."
            )

        car = reservation.car
        RentalService._assert_no_conflicting_rental(
            car_id=car.pk,
            start_at=reservation.start_at,
            end_at=reservation.end_at,
        )
        if get_overlapping_reservations(
            car.pk,
            reservation.start_at,
            reservation.end_at,
            exclude_reservation_id=reservation.pk,
        ).exists():
            raise ValidationError(
                "W tym przedziale istnieje inna rezerwacja dla tego pojazdu."
            )
        if not AvailabilityService.is_car_available(
            car,
            reservation.start_at,
            reservation.end_at,
            exclude_reservation_id=reservation.pk,
        ):
            raise ValidationError(
                "Pojazd jest niedostepny w terminie rezerwacji "
                "(blokada lub inna rezerwacja)."
            )

        rental = Rental(
            reservation=reservation,
            status=RentalStatus.SCHEDULED,
            scheduled_start_at=reservation.start_at,
            scheduled_end_at=reservation.end_at,
            deposit_amount=car.category.deposit,
            notes=notes or reservation.notes,
            created_by_id=created_by_id,
        )
        rental.full_clean()
        rental.save()

        reservation.status = ReservationStatus.CONVERTED_TO_RENTAL
        reservation.save(update_fields=["status", "updated_at"])
        return rental

    @staticmethod
    @transaction.atomic
    def start(
        rental: Rental,
        *,
        at: datetime | None = None,
    ) -> Rental:
        RentalService._assert_can_mutate(rental)
        if rental.status != RentalStatus.SCHEDULED:
            raise ValidationError(
                "Rozpoczac mozna tylko wynajem w statusie zaplanowany."
            )

        started = at or timezone.now()
        rental.status = RentalStatus.ACTIVE
        rental.actual_start_at = started
        rental.save(update_fields=["status", "actual_start_at", "updated_at"])
        return rental

    @staticmethod
    @transaction.atomic
    def mark_returned(
        rental: Rental,
        *,
        at: datetime | None = None,
    ) -> Rental:
        RentalService._assert_can_mutate(rental)
        if rental.status != RentalStatus.ACTIVE:
            raise ValidationError(
                "Zwrot mozna zarejestrowac tylko dla aktywnego wynajmu."
            )

        returned = at or timezone.now()
        rental.status = RentalStatus.RETURNED
        rental.actual_end_at = returned
        rental.save(update_fields=["status", "actual_end_at", "updated_at"])
        return rental

    @staticmethod
    @transaction.atomic
    def close(rental: Rental) -> Rental:
        RentalService._assert_can_mutate(rental)
        if rental.status != RentalStatus.RETURNED:
            raise ValidationError(
                "Zamknac mozna tylko wynajem po zarejestrowanym zwrocie."
            )

        rental.status = RentalStatus.CLOSED
        rental.closed_at = timezone.now()
        rental.save(update_fields=["status", "closed_at", "updated_at"])
        return rental

    @staticmethod
    @transaction.atomic
    def cancel(
        rental: Rental,
        *,
        reason: str = "",
    ) -> Rental:
        RentalService._assert_can_mutate(rental)
        if rental.status != RentalStatus.SCHEDULED:
            raise ValidationError(
                "Anulowac mozna tylko wynajem zaplanowany (przed wydaniem)."
            )

        rental.status = RentalStatus.CANCELLED
        rental.cancellation_reason = reason
        rental.cancelled_at = timezone.now()
        rental.save(
            update_fields=[
                "status",
                "cancellation_reason",
                "cancelled_at",
                "updated_at",
            ]
        )
        return rental
