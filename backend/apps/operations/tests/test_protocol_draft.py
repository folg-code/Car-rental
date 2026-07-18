"""Testy draftu protokolu wydania (Faza B/C)."""

from decimal import Decimal

import pytest

from apps.fleet.models import CarEquipment, EquipmentItem
from apps.operations.models import ProtocolStatus
from apps.operations.services.handover import HandoverService
from apps.operations.tests.test_operations import _tiny_image


@pytest.mark.django_db
def test_handover_draft_persists_across_steps(scheduled_rental) -> None:
    car = scheduled_rental.reservation.car
    car.fuel_tank_capacity_liters = Decimal("45.0")
    car.save(update_fields=["fuel_tank_capacity_liters"])
    item = EquipmentItem.objects.create(code="main_key", name="Kluczyk")
    CarEquipment.objects.create(car=car, item=item, quantity=1)

    handover = HandoverService.start_handover(scheduled_rental.pk)
    assert handover.status == ProtocolStatus.DRAFT
    assert handover.equipment_lines.count() == 1

    HandoverService.save_driver(
        handover,
        data={
            "first_name": "Jan",
            "last_name": "Test",
            "document_verified": True,
            "license_valid": True,
            "license_category_ok": True,
        },
    )
    HandoverService.save_odometer(handover, mileage=10_100, fuel_level_percent=100)
    handover.refresh_from_db()
    assert handover.mileage == 10_100
    assert handover.fuel_level_percent == 100
    assert handover.current_step == "damages"

    marker = HandoverService.add_damage_marker(
        handover,
        damage_type="R",
        description="Rysa testowa",
        pos_x=Decimal("40"),
        pos_y=Decimal("60"),
    )
    assert marker.is_new

    HandoverService.save_equipment(handover, lines=[], confirm_all=True)
    handover.refresh_from_db()
    assert handover.status == ProtocolStatus.READY_FOR_SIGNATURE

    HandoverService.finalize_handover(
        handover,
        signer_name="Jan Test",
        signature_image=_tiny_image(),
    )
    handover.refresh_from_db()
    assert handover.is_completed
    assert handover.is_locked
