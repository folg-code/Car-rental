from __future__ import annotations

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

    def as_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "location": self.location,
            "severity": self.severity,
            "severity_label": self.severity_label,
            "is_new": self.is_new,
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

    def as_template_context(self) -> dict[str, Any]:
        return {
            "rental_id": self.rental_id,
            "customer_name": self.customer_name,
            "car_label": self.car_label,
            "registration_number": self.registration_number,
            "mileage": self.mileage,
            "fuel_level_percent": self.fuel_level_percent,
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

    def as_template_context(self) -> dict[str, Any]:
        return {
            "rental_id": self.rental_id,
            "customer_name": self.customer_name,
            "car_label": self.car_label,
            "registration_number": self.registration_number,
            "handover_mileage": self.handover_mileage,
            "handover_fuel_level_percent": self.handover_fuel_level_percent,
            "mileage": self.mileage,
            "fuel_level_percent": self.fuel_level_percent,
            "mileage_driven": self.mileage_driven,
            "notes": self.notes,
            "surcharge_notes": self.surcharge_notes,
            "completed_at": self.completed_at,
            "damages": [d.as_dict() for d in self.damages],
            "signature_name": self.signature_name,
            "signature_uri": self.signature_uri,
        }


def image_field_to_uri(image_field) -> str | None:
    if not image_field or not image_field.name:
        return None
    path = Path(image_field.path)
    if path.is_file():
        return path.as_uri()
    return None
