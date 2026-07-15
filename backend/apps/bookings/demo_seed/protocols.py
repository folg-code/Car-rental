"""Syntetyczne protokoły wydania/zwrotu dla danych demo (bez podpisu i PDF)."""

from datetime import datetime

from apps.bookings.models import Rental
from apps.operations.models import HandoverProtocol, ReturnProtocol


def seed_completed_handover(
    rental: Rental,
    *,
    at: datetime,
    mileage: int | None = None,
) -> HandoverProtocol:
    car = rental.reservation.car
    odometer = mileage if mileage is not None else car.mileage
    handover, _ = HandoverProtocol.objects.update_or_create(
        rental=rental,
        defaults={
            "mileage": odometer,
            "fuel_level_percent": 100,
            "notes": "DEMO_SEED",
            "completed_at": at,
        },
    )
    return handover


def seed_completed_return(
    rental: Rental,
    handover: HandoverProtocol,
    *,
    at: datetime,
    driven_km: int = 150,
    fuel_level_percent: int | None = None,
) -> ReturnProtocol:
    if fuel_level_percent is None:
        fuel_level_percent = max(0, handover.fuel_level_percent - 15)
    return_protocol, _ = ReturnProtocol.objects.update_or_create(
        rental=rental,
        defaults={
            "handover": handover,
            "mileage": handover.mileage + driven_km,
            "fuel_level_percent": fuel_level_percent,
            "notes": "DEMO_SEED",
            "completed_at": at,
        },
    )
    return return_protocol
