from django.core.exceptions import ObjectDoesNotExist, ValidationError

from apps.documents.dto.protocol import (
    DamageSnapshotData,
    HandoverDocumentData,
    ReturnDocumentData,
    image_field_to_uri,
)
from apps.operations.models import DamageSnapshot, HandoverProtocol, ReturnProtocol


def _snapshot_to_data(snapshot: DamageSnapshot) -> DamageSnapshotData:
    return DamageSnapshotData(
        description=snapshot.description,
        location=snapshot.location,
        severity=snapshot.severity,
        severity_label=snapshot.get_severity_display(),
        is_new=snapshot.is_new_at_protocol,
        damage_type=snapshot.damage_type or "U",
        pos_x=str(snapshot.pos_x) if snapshot.pos_x is not None else "",
        pos_y=str(snapshot.pos_y) if snapshot.pos_y is not None else "",
    )


def _car_label_from_reservation(reservation) -> str:
    car = reservation.car
    return f"{car.make} {car.model}"


def _safe_signature_uri(signature) -> str | None:
    if signature is None or not getattr(signature, "image", None):
        return None
    return image_field_to_uri(signature.image)


def build_handover_document_data(handover: HandoverProtocol) -> HandoverDocumentData:
    if not handover.is_completed:
        raise ValidationError("PDF wydania wymaga zakonczonego protokolu wydania.")

    reservation = handover.rental.reservation
    customer = reservation.customer
    car = reservation.car

    try:
        signature = handover.signature
    except ObjectDoesNotExist:
        signature = None

    try:
        driver = handover.driver
        driver_name = f"{driver.first_name} {driver.last_name}".strip()
    except ObjectDoesNotExist:
        driver_name = customer.full_name

    damages = tuple(
        _snapshot_to_data(s)
        for s in handover.damage_snapshots.all().order_by("captured_at", "pk")
    )
    equipment = tuple(
        f"{line.name_snapshot} x{line.quantity_actual or line.quantity_expected}"
        f" ({line.get_status_display()})"
        for line in handover.equipment_lines.all()
    )

    return HandoverDocumentData(
        rental_id=handover.rental_id,
        handover_protocol_id=handover.pk,
        customer_name=customer.full_name,
        car_label=_car_label_from_reservation(reservation),
        registration_number=car.registration_number,
        mileage=handover.mileage or 0,
        fuel_level_percent=handover.fuel_level_percent or 0,
        fuel_level=handover.fuel_level or "",
        driver_name=driver_name,
        equipment_lines=equipment,
        notes=handover.notes,
        completed_at=handover.completed_at,
        damages=damages,
        signature_name=signature.signer_name if signature else "",
        signature_uri=_safe_signature_uri(signature),
    )


def build_return_document_data(return_protocol: ReturnProtocol) -> ReturnDocumentData:
    if not return_protocol.is_completed:
        raise ValidationError("PDF zwrotu wymaga zakonczonego protokolu zwrotu.")

    handover = return_protocol.handover
    reservation = return_protocol.rental.reservation
    customer = reservation.customer
    car = reservation.car

    try:
        signature = return_protocol.signature
    except ObjectDoesNotExist:
        signature = None

    damages = tuple(
        _snapshot_to_data(s)
        for s in return_protocol.damage_snapshots.all().order_by("captured_at", "pk")
    )
    settlement = tuple(
        f"{line.name}: {line.amount} PLN ({line.get_decision_display()})"
        for line in return_protocol.settlement_lines.all()
    )
    cleanliness = return_protocol.cleanliness or {}
    cleanliness_summary = ", ".join(f"{k}={v}" for k, v in cleanliness.items() if v)

    return ReturnDocumentData(
        rental_id=return_protocol.rental_id,
        return_protocol_id=return_protocol.pk,
        handover_protocol_id=handover.pk,
        customer_name=customer.full_name,
        car_label=_car_label_from_reservation(reservation),
        registration_number=car.registration_number,
        handover_mileage=handover.mileage or 0,
        handover_fuel_level_percent=handover.fuel_level_percent or 0,
        handover_fuel_level=handover.fuel_level or "",
        mileage=return_protocol.mileage or 0,
        fuel_level_percent=return_protocol.fuel_level_percent or 0,
        fuel_level=return_protocol.fuel_level or "",
        mileage_driven=return_protocol.mileage_driven,
        notes=return_protocol.notes,
        surcharge_notes=return_protocol.surcharge_notes,
        settlement_lines=settlement,
        cleanliness_summary=cleanliness_summary,
        completed_at=return_protocol.completed_at,
        damages=damages,
        signature_name=signature.signer_name if signature else "",
        signature_uri=_safe_signature_uri(signature),
    )


def get_handover_document_data(handover_id: int) -> HandoverDocumentData:
    handover = (
        HandoverProtocol.objects.select_related(
            "rental",
            "rental__reservation",
            "rental__reservation__customer",
            "rental__reservation__car",
            "signature",
            "driver",
        )
        .prefetch_related("damage_snapshots", "equipment_lines")
        .filter(pk=handover_id)
        .first()
    )
    if handover is None:
        raise ValidationError(f"Protokol wydania {handover_id} nie istnieje.")
    return build_handover_document_data(handover)


def get_return_document_data(return_protocol_id: int) -> ReturnDocumentData:
    return_protocol = (
        ReturnProtocol.objects.select_related(
            "rental",
            "rental__reservation",
            "rental__reservation__customer",
            "rental__reservation__car",
            "handover",
            "signature",
        )
        .prefetch_related("damage_snapshots", "settlement_lines")
        .filter(pk=return_protocol_id)
        .first()
    )
    if return_protocol is None:
        raise ValidationError(f"Protokol zwrotu {return_protocol_id} nie istnieje.")
    return build_return_document_data(return_protocol)
