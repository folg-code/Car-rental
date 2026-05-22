from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.bookings.models import (
    BLOCKING_RESERVATION_STATUSES,
    Reservation,
    ReservationStatus,
)
from apps.bookings.selectors.availability import get_overlapping_reservations
from apps.fleet.models import Car
from apps.fleet.services.availability import AvailabilityService


class ReservationService:
    @staticmethod
    def _assert_can_mutate(reservation: Reservation) -> None:
        if reservation.is_terminal:
            msg = "Rezerwacja w statusie koncowym nie moze byc zmieniana."
            raise ValidationError(msg)

    @staticmethod
    def _assert_available(
        *,
        car: Car,
        start_at: datetime,
        end_at: datetime,
        exclude_reservation_id: int | None = None,
    ) -> None:
        AvailabilityService.validate_interval(start_at, end_at)

        if get_overlapping_reservations(
            car.pk,
            start_at,
            end_at,
            exclude_reservation_id=exclude_reservation_id,
        ).exists():
            raise ValidationError(
                "W tym przedziale istnieje juz rezerwacja dla tego pojazdu."
            )

        if not AvailabilityService.is_car_available(
            car,
            start_at,
            end_at,
            exclude_reservation_id=exclude_reservation_id,
        ):
            raise ValidationError(
                "Pojazd jest niedostepny w wybranym przedziale "
                "(status, blokada lub rezerwacja)."
            )

    @staticmethod
    def create(
        *,
        customer_id: int,
        car_id: int,
        start_at: datetime,
        end_at: datetime,
        status: str = ReservationStatus.DRAFT,
        notes: str = "",
        created_by_id: int | None = None,
    ) -> Reservation:
        if status not in ReservationStatus.values:
            msg = f"Nieprawidlowy status rezerwacji: {status}"
            raise ValueError(msg)

        car = Car.objects.filter(pk=car_id).first()
        if car is None:
            msg = f"Pojazd {car_id} nie istnieje."
            raise ValueError(msg)

        reservation = Reservation(
            customer_id=customer_id,
            car_id=car_id,
            start_at=start_at,
            end_at=end_at,
            status=status,
            notes=notes,
            created_by_id=created_by_id,
        )
        reservation.full_clean()

        if status in BLOCKING_RESERVATION_STATUSES:
            ReservationService._assert_available(
                car=car,
                start_at=start_at,
                end_at=end_at,
            )

        reservation.save()
        return reservation

    @staticmethod
    def confirm(reservation: Reservation) -> Reservation:
        ReservationService._assert_can_mutate(reservation)
        if reservation.status not in (
            ReservationStatus.DRAFT,
            ReservationStatus.PENDING_PAYMENT,
        ):
            raise ValidationError(
                "Potwierdzic mozna tylko rezerwacje "
                "w statusie szkic lub oczekuje platnosci."
            )

        ReservationService._assert_available(
            car=reservation.car,
            start_at=reservation.start_at,
            end_at=reservation.end_at,
            exclude_reservation_id=reservation.pk,
        )
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])
        return reservation

    @staticmethod
    def cancel(
        reservation: Reservation,
        *,
        reason: str = "",
    ) -> Reservation:
        ReservationService._assert_can_mutate(reservation)
        if reservation.status == ReservationStatus.CANCELLED:
            raise ValidationError("Rezerwacja jest juz anulowana.")

        reservation.status = ReservationStatus.CANCELLED
        reservation.cancellation_reason = reason
        reservation.cancelled_at = timezone.now()
        reservation.save(
            update_fields=[
                "status",
                "cancellation_reason",
                "cancelled_at",
                "updated_at",
            ]
        )
        return reservation

    @staticmethod
    def expire(reservation: Reservation) -> Reservation:
        ReservationService._assert_can_mutate(reservation)
        if reservation.status not in (
            ReservationStatus.DRAFT,
            ReservationStatus.PENDING_PAYMENT,
        ):
            raise ValidationError(
                "Wygasic mozna tylko rezerwacje "
                "w statusie szkic lub oczekuje platnosci."
            )

        reservation.status = ReservationStatus.EXPIRED
        reservation.save(update_fields=["status", "updated_at"])
        return reservation

    @staticmethod
    def update(
        reservation: Reservation,
        *,
        customer_id: int | None = None,
        car_id: int | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> Reservation:
        ReservationService._assert_can_mutate(reservation)

        if customer_id is not None:
            reservation.customer_id = customer_id
        if car_id is not None:
            reservation.car_id = car_id
        if start_at is not None:
            reservation.start_at = start_at
        if end_at is not None:
            reservation.end_at = end_at
        if notes is not None:
            reservation.notes = notes
        if status is not None:
            if status not in ReservationStatus.values:
                msg = f"Nieprawidlowy status rezerwacji: {status}"
                raise ValueError(msg)
            reservation.status = status

        reservation.full_clean()
        car = Car.objects.get(pk=reservation.car_id)

        if reservation.status in BLOCKING_RESERVATION_STATUSES:
            ReservationService._assert_available(
                car=car,
                start_at=reservation.start_at,
                end_at=reservation.end_at,
                exclude_reservation_id=reservation.pk,
            )

        reservation.save()
        return reservation
