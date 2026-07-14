from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.bookings.constants import RESERVATION_EMAIL_PENDING
from apps.bookings.models import (
    Customer,
    Reservation,
    ReservationPricingMode,
    ReservationStatus,
)
from apps.bookings.services.customer import CustomerService
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.reservation import ReservationService
from apps.bookings.services.reservation_email import ReservationEmailService
from apps.bookings.services.reservation_sms import ReservationSmsService
from apps.fleet.models import Car, CarStatus


@dataclass(frozen=True, slots=True)
class PublicBookingResult:
    """Wynik rezerwacji online (task 8.12)."""

    reservation: Reservation
    customer: Customer
    customer_created: bool


class PublicBookingOrchestrator:
    """Orkiestracja publicznego POST rezerwacji — tylko serwisy domenowe."""

    @staticmethod
    @transaction.atomic
    def submit(
        *,
        car: Car,
        start_at: datetime,
        end_at: datetime,
        first_name: str,
        last_name: str,
        email: str = "",
        phone: str = "",
        extra_codes: list[str] | None = None,
        notes: str = "",
    ) -> PublicBookingResult:
        if car.status != CarStatus.ACTIVE:
            raise ValidationError("Wybrane auto nie jest dostepne do rezerwacji.")

        customer, customer_created = CustomerService.get_or_create_for_public_booking(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start_at,
            end_at=end_at,
            status=ReservationStatus.PENDING_PAYMENT,
            notes=notes.strip(),
            pricing_mode=ReservationPricingMode.AUTO,
        )
        codes = extra_codes or []
        if codes:
            PriceSnapshotService.freeze(
                reservation,
                extra_codes=codes,
                replace=True,
            )
        reservation_id = reservation.pk
        transaction.on_commit(
            lambda: ReservationEmailService.enqueue_reservation_email(
                reservation_id,
                email_kind=RESERVATION_EMAIL_PENDING,
            ),
        )
        transaction.on_commit(
            lambda: ReservationSmsService.enqueue_reservation_sms(
                reservation_id,
                sms_kind=RESERVATION_EMAIL_PENDING,
            ),
        )
        return PublicBookingResult(
            reservation=reservation,
            customer=customer,
            customer_created=customer_created,
        )
