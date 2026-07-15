"""Dokumenty floty, blokady dostepnosci i uszkodzenia dla demo."""

from __future__ import annotations

from datetime import timedelta

from django.core.files.base import ContentFile
from django.utils import timezone

from apps.bookings.demo_seed.catalog import demo_note
from apps.fleet.models import (
    AvailabilityBlock,
    AvailabilityBlockType,
    Car,
    CarDocument,
    CarDocumentType,
    Damage,
    DamageSeverity,
    DamageStatus,
)


def _demo_pdf(name: str) -> ContentFile:
    return ContentFile(b"%PDF-1.4 demo", name=name)


def seed_fleet_extras(
    *,
    cars: dict[str, Car],
    panel_user_id: int | None,
) -> tuple[int, int, int]:
    """Zwraca (dokumenty, blokady, uszkodzenia) utworzone w tej sesji."""
    docs = _seed_car_documents(cars)
    blocks = _seed_availability_blocks(cars, panel_user_id)
    damages = _seed_damages(cars)
    return docs, blocks, damages


def _seed_car_documents(cars: dict[str, Car]) -> int:
    today = timezone.localdate()
    specs = (
        (
            "KR1DEMO3",
            CarDocumentType.INSURANCE,
            today + timedelta(days=14),
            "OC/AC — wygasa wkrotce",
        ),
        (
            "KR1DEMO6",
            CarDocumentType.INSPECTION,
            today + timedelta(days=180),
            "Przeglad OK",
        ),
        (
            "KR1DEMO7",
            CarDocumentType.REGISTRATION,
            None,
            "Dowod rejestracyjny",
        ),
    )
    created = 0
    for reg, doc_type, valid_until, _note in specs:
        car = cars.get(reg)
        if car is None:
            continue
        marker = demo_note(f"fleet-doc:{reg}:{doc_type}")
        if CarDocument.objects.filter(car=car, notes=marker).exists():
            continue
        CarDocument.objects.create(
            car=car,
            document_type=doc_type,
            file=_demo_pdf(f"{reg}-{doc_type}.pdf"),
            valid_until=valid_until,
            notes=marker,
        )
        created += 1
    return created


def _seed_availability_blocks(
    cars: dict[str, Car],
    panel_user_id: int | None,
) -> int:
    car = cars.get("KR1DEMO5")
    if car is None:
        return 0
    marker = demo_note("fleet-block:KR1DEMO5")
    if AvailabilityBlock.objects.filter(car=car, reason=marker).exists():
        return 0
    start = timezone.now() + timedelta(days=20)
    end = start + timedelta(days=3)
    AvailabilityBlock.objects.create(
        car=car,
        start_at=start,
        end_at=end,
        block_type=AvailabilityBlockType.SERVICE,
        reason=marker,
        created_by_id=panel_user_id,
    )
    return 1


def _seed_damages(cars: dict[str, Car]) -> int:
    specs = (
        (
            "KR1DEMO4",
            "Rysa na zderzaku tylnym",
            "zderzak tylny",
            DamageSeverity.MINOR,
            DamageStatus.ACTIVE,
        ),
        (
            "KR1DEMO3",
            "Wgniecenie drzwi prawych tylnych (naprawione)",
            "drzwi prawe tylne",
            DamageSeverity.MODERATE,
            DamageStatus.REPAIRED,
        ),
    )
    created = 0
    for reg, description, location, severity, status in specs:
        car = cars.get(reg)
        if car is None:
            continue
        marker = demo_note(f"damage:{reg}:{location}")
        if Damage.objects.filter(car=car, description__startswith=marker).exists():
            continue
        damage = Damage.objects.create(
            car=car,
            description=f"{marker} — {description}",
            location=location,
            severity=severity,
            status=status,
        )
        if status == DamageStatus.REPAIRED:
            damage.repaired_at = timezone.now() - timedelta(days=30)
            damage.save(update_fields=["repaired_at"])
        created += 1
    return created
