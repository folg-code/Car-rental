from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DamageSnapshotData:
    description: str
    location: str
    severity: str
    severity_label: str
    is_new: bool
    damage_type: str = "U"
    pos_x: str = ""
    pos_y: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "location": self.location,
            "severity": self.severity,
            "severity_label": self.severity_label,
            "is_new": self.is_new,
            "damage_type": self.damage_type,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
        }


@dataclass(frozen=True, slots=True)
class HandoverDocumentData:
    """Immutable payload for handover protocol PDF
    — built from protocol snapshots only."""

    rental_id: int
    handover_protocol_id: int
    customer_name: str
    car_label: str
    registration_number: str
    mileage: int
    fuel_level_percent: int
    notes: str
    completed_at: datetime
    damages: tuple[DamageSnapshotData, ...]
    signature_name: str
    signature_uri: str | None
    fuel_level: str = ""
    driver_name: str = ""
    equipment_lines: tuple[str, ...] = ()

    def as_template_context(self) -> dict[str, Any]:
        return {
            "rental_id": self.rental_id,
            "customer_name": self.customer_name,
            "car_label": self.car_label,
            "registration_number": self.registration_number,
            "mileage": self.mileage,
            "fuel_level_percent": self.fuel_level_percent,
            "fuel_level": self.fuel_level,
            "driver_name": self.driver_name,
            "equipment_lines": list(self.equipment_lines),
            "notes": self.notes,
            "completed_at": self.completed_at,
            "damages": [d.as_dict() for d in self.damages],
            "signature_name": self.signature_name,
            "signature_uri": self.signature_uri,
        }


@dataclass(frozen=True, slots=True)
class ReturnDocumentData:
    """Immutable payload for return protocol PDF
    — includes frozen handover comparison."""

    rental_id: int
    return_protocol_id: int
    handover_protocol_id: int
    customer_name: str
    car_label: str
    registration_number: str
    handover_mileage: int
    handover_fuel_level_percent: int
    mileage: int
    fuel_level_percent: int
    mileage_driven: int | None
    notes: str
    surcharge_notes: str
    completed_at: datetime
    damages: tuple[DamageSnapshotData, ...]
    signature_name: str
    signature_uri: str | None
    fuel_level: str = ""
    handover_fuel_level: str = ""
    settlement_lines: tuple[str, ...] = ()
    cleanliness_summary: str = ""

    def as_template_context(self) -> dict[str, Any]:
        return {
            "rental_id": self.rental_id,
            "customer_name": self.customer_name,
            "car_label": self.car_label,
            "registration_number": self.registration_number,
            "handover_mileage": self.handover_mileage,
            "handover_fuel_level_percent": self.handover_fuel_level_percent,
            "handover_fuel_level": self.handover_fuel_level,
            "mileage": self.mileage,
            "fuel_level_percent": self.fuel_level_percent,
            "fuel_level": self.fuel_level,
            "mileage_driven": self.mileage_driven,
            "notes": self.notes,
            "surcharge_notes": self.surcharge_notes,
            "settlement_lines": list(self.settlement_lines),
            "cleanliness_summary": self.cleanliness_summary,
            "completed_at": self.completed_at,
            "damages": [d.as_dict() for d in self.damages],
            "signature_name": self.signature_name,
            "signature_uri": self.signature_uri,
        }


def image_field_to_uri(image_field) -> str | None:
    """Osadza obraz inline — WeasyPrint na CI nie laduje niezawodnie file:// URI."""
    if not image_field or not image_field.name:
        return None
    path = Path(image_field.path)
    if not path.is_file():
        return None
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
