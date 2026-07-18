"""Weryfikacja scenariuszy krytycznych dla ścieżki prezentacji demo."""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model

from apps.bookings.demo_seed.catalog import (
    DEMO_CUSTOMER_USERNAME,
    DEMO_MANAGER_USERNAME,
    DEMO_PANEL_USERNAME,
    demo_note,
)
from apps.bookings.models import Customer, Rental, RentalStatus, Reservation
from apps.payments.models import RentalCharge

User = get_user_model()

# Klucze wymagane do ścieżki prezentacji end-to-end (runbook).
PRESENTATION_SCENARIO_KEYS: tuple[str, ...] = (
    "ops-handover-today",
    "ops-return-surcharges",
    "ops-active",
    "res-pending-payment",
)


@dataclass(frozen=True, slots=True)
class PresentationCheckResult:
    ok: bool
    errors: tuple[str, ...]

    def raise_if_failed(self) -> None:
        if not self.ok:
            joined = "; ".join(self.errors)
            msg = f"Presentation seed check failed: {joined}"
            raise RuntimeError(msg)


def verify_presentation_seed() -> PresentationCheckResult:
    """Sprawdza konta i scenariusze potrzebne do prezentacji demo."""
    errors: list[str] = []

    for username in (
        DEMO_PANEL_USERNAME,
        DEMO_MANAGER_USERNAME,
        DEMO_CUSTOMER_USERNAME,
    ):
        if not User.objects.filter(username=username).exists():
            errors.append(f"brak konta `{username}`")

    for key in PRESENTATION_SCENARIO_KEYS:
        if not Reservation.objects.filter(notes__startswith=demo_note(key)).exists():
            errors.append(f"brak scenariusza `{key}`")

    handover = Rental.objects.filter(
        reservation__notes__startswith=demo_note("ops-handover-today"),
        status=RentalStatus.SCHEDULED,
    ).first()
    if handover is None:
        errors.append("ops-handover-today: brak wynajmu w statusie scheduled")

    returned = Rental.objects.filter(
        reservation__notes__startswith=demo_note("ops-return-surcharges"),
        status=RentalStatus.RETURNED,
    ).first()
    if returned is None:
        errors.append("ops-return-surcharges: brak wynajmu w statusie returned")
    elif not RentalCharge.objects.filter(rental=returned).exists():
        errors.append("ops-return-surcharges: brak dopłat (RentalCharge)")

    active = Rental.objects.filter(
        reservation__notes__startswith=demo_note("ops-active"),
        status=RentalStatus.ACTIVE,
    ).first()
    if active is None:
        errors.append("ops-active: brak wynajmu w statusie active")

    portal_user = User.objects.filter(username=DEMO_CUSTOMER_USERNAME).first()
    if (
        portal_user is not None
        and not Customer.objects.filter(user=portal_user).exists()
    ):
        errors.append("portal: konto `klient` nie jest powiązane z Customer")

    return PresentationCheckResult(ok=not errors, errors=tuple(errors))
