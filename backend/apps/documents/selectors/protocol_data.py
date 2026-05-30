from django.core.exceptions import ValidationError

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
    )


def _car_label_from_reservation(reservation) -> str:
    car = reservation.car
    return f"{car.make} {car.model}"


def build_handover_document_data(handover: HandoverProtocol) -> HandoverDocumentData:
    if not handover.is_completed:
        raise ValidationError("PDF wydania wymaga zakonczonego protokolu wydania.")

    reservation = handover.rental.reservation
    customer = reservation.customer
    car = reservation.car

    signature = getattr(handover, "signature", None)
    damages = tuple(
        _snapshot_to_data(s)
        for s in handover.damage_snapshots.all().order_by("captured_at", "pk")
    )

    return HandoverDocumentData(
        rental_id=handover.rental_id,
        handover_protocol_id=handover.pk,
        customer_name=customer.full_name,
        car_label=_car_label_from_reservation(reservation),
        registration_number=car.registration_number,
        mileage=handover.mileage,
        fuel_level_percent=handover.fuel_level_percent,
        notes=handover.notes,
        completed_at=handover.completed_at,
        damages=damages,
        signature_name=signature.signer_name if signature else "",
        signature_uri=image_field_to_uri(signature.image) if signature else None,
    )


def build_return_document_data(return_protocol: ReturnProtocol) -> ReturnDocumentData:
    if not return_protocol.is_completed:
        raise ValidationError("PDF zwrotu wymaga zakonczonego protokolu zwrotu.")

    handover = return_protocol.handover
    reservation = return_protocol.rental.reservation
    customer = reservation.customer
    car = reservation.car

    signature = getattr(return_protocol, "signature", None)
    damages = tuple(
        _snapshot_to_data(s)
        for s in return_protocol.damage_snapshots.all().order_by("captured_at", "pk")
    )

    return ReturnDocumentData(
        rental_id=return_protocol.rental_id,
        return_protocol_id=return_protocol.pk,
        handover_protocol_id=handover.pk,
        customer_name=customer.full_name,
        car_label=_car_label_from_reservation(reservation),
        registration_number=car.registration_number,
        handover_mileage=handover.mileage,
        handover_fuel_level_percent=handover.fuel_level_percent,
        mileage=return_protocol.mileage,
        fuel_level_percent=return_protocol.fuel_level_percent,
        mileage_driven=return_protocol.mileage_driven,
        notes=return_protocol.notes,
        surcharge_notes=return_protocol.surcharge_notes,
        completed_at=return_protocol.completed_at,
        damages=damages,
        signature_name=signature.signer_name if signature else "",
        signature_uri=image_field_to_uri(signature.image) if signature else None,
    )


def get_handover_document_data(handover_id: int) -> HandoverDocumentData:
    handover = (
        HandoverProtocol.objects.select_related(
            "rental",
            "rental__reservation",
            "rental__reservation__customer",
            "rental__reservation__car",
            "signature",
        )
        .prefetch_related("damage_snapshots")
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
        .prefetch_related("damage_snapshots")
        .filter(pk=return_protocol_id)
        .first()
    )
    if return_protocol is None:
        raise ValidationError(f"Protokol zwrotu {return_protocol_id} nie istnieje.")
    return build_return_document_data(return_protocol)
