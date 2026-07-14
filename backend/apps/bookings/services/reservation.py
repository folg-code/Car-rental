from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services.audit import AuditService
from apps.bookings.constants import RESERVATION_EMAIL_CONFIRMED
from apps.bookings.models import (
    BLOCKING_RESERVATION_STATUSES,
    Rental,
    Reservation,
    ReservationPricingMode,
    ReservationStatus,
)
from apps.bookings.selectors.availability import get_overlapping_reservations
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation_email import ReservationEmailService
from apps.bookings.services.reservation_sms import ReservationSmsService
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
        pricing_mode: str = ReservationPricingMode.AUTO,
        price_list_id: int | None = None,
        custom_total: Decimal | None = None,
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
            pricing_mode=pricing_mode,
            price_list_id=price_list_id,
            custom_total=custom_total,
        )
        reservation.full_clean()

        if status in BLOCKING_RESERVATION_STATUSES:
            ReservationService._assert_available(
                car=car,
                start_at=start_at,
                end_at=end_at,
            )

        reservation.save()
        if status in (
            ReservationStatus.PENDING_PAYMENT,
            ReservationStatus.CONFIRMED,
        ) or PriceSnapshotService.can_recalculate(reservation):
            PriceSnapshotService.freeze(reservation)
        return reservation

    @staticmethod
    @transaction.atomic
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
        PriceSnapshotService.freeze(reservation)
        old_status = reservation.status
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])
        AuditService.log_status_change(
            AuditAction.RESERVATION_CONFIRMED,
            reservation_id=reservation.pk,
            old_status=old_status,
            new_status=reservation.status,
        )
        reservation_id = reservation.pk
        transaction.on_commit(
            lambda: ReservationEmailService.enqueue_reservation_email(
                reservation_id,
                email_kind=RESERVATION_EMAIL_CONFIRMED,
            ),
        )
        transaction.on_commit(
            lambda: ReservationSmsService.enqueue_reservation_sms(
                reservation_id,
                sms_kind=RESERVATION_EMAIL_CONFIRMED,
            ),
        )
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

        old_status = reservation.status
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
        AuditService.log_status_change(
            AuditAction.RESERVATION_CANCELLED,
            reservation_id=reservation.pk,
            old_status=old_status,
            new_status=reservation.status,
            metadata={"reason": reason},
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
        pricing_mode: str | None = None,
        price_list_id: int | None = None,
        custom_total: Decimal | None = None,
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
        if pricing_mode is not None:
            reservation.pricing_mode = pricing_mode
            if pricing_mode == ReservationPricingMode.AUTO:
                reservation.price_list_id = None
                reservation.custom_total = None
            elif pricing_mode == ReservationPricingMode.PRICE_LIST:
                reservation.price_list_id = price_list_id
                reservation.custom_total = None
            elif pricing_mode == ReservationPricingMode.CUSTOM:
                reservation.price_list_id = None
                reservation.custom_total = custom_total
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
        if PriceSnapshotService.can_recalculate(reservation):
            PriceSnapshotService.freeze(reservation)
        return reservation

    @staticmethod
    @transaction.atomic
    def convert_to_rental(
        reservation: Reservation,
        *,
        created_by_id: int | None = None,
        notes: str = "",
    ) -> Rental:
        return RentalService.convert_from_reservation(
            reservation,
            created_by_id=created_by_id,
            notes=notes,
        )
