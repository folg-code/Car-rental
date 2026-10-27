from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services.audit import AuditService
from apps.bookings.models import Rental, RentalStatus
from apps.bookings.services.rental import RentalService
from apps.documents.services.document import DocumentService
from apps.fleet.fuel import percent_to_fuel_level
from apps.fleet.models import Car, CarEquipment, DamageType
from apps.fleet.services.damage import DamageService
from apps.operations.models import (
    DamageMarkerResolution,
    EquipmentLineStatus,
    HandoverProtocol,
    ProtocolDamageMarker,
    ProtocolDriver,
    ProtocolEquipmentLine,
    ProtocolPhoto,
    ProtocolPhotoCategory,
    ProtocolStatus,
    Signature,
    SignatureOutcome,
)
from apps.operations.services.damage_snapshot import DamageSnapshotService
from config.upload_validation import validate_image_upload, validate_image_uploads


class HandoverService:
    @staticmethod
    def _get_rental_for_handover(rental_id: int) -> Rental:
        rental = (
            Rental.objects.select_related(
                "reservation",
                "reservation__car",
                "reservation__customer",
            )
            .filter(pk=rental_id)
            .first()
        )
        if rental is None:
            raise ValidationError(f"Wynajem {rental_id} nie istnieje.")
        if rental.status == RentalStatus.SCHEDULED:
            return rental
        if rental.status == RentalStatus.ACTIVE:
            handover = (
                HandoverProtocol.objects.filter(rental_id=rental_id)
                .only("completed_at", "status")
                .first()
            )
            if handover is None or not handover.is_completed:
                return rental
        raise ValidationError(
            "Protokol wydania mozna zlozyc tylko dla wynajmu zaplanowanego "
            "lub aktywnego bez zakonczonego protokolu."
        )

    @staticmethod
    def _ensure_editable(handover: HandoverProtocol) -> None:
        if handover.is_locked:
            raise ValidationError("Protokol wydania jest zamkniety — brak edycji.")

    @staticmethod
    @transaction.atomic
    def start_handover(rental_id: int) -> HandoverProtocol:
        rental = HandoverService._get_rental_for_handover(rental_id)
        handover, created = HandoverProtocol.objects.get_or_create(
            rental=rental,
            defaults={
                "status": ProtocolStatus.DRAFT,
                "current_step": "driver",
            },
        )
        if handover.is_locked:
            raise ValidationError("Protokol wydania jest juz zakonczony.")
        if created or not ProtocolDriver.objects.filter(handover=handover).exists():
            customer = rental.reservation.customer
            ProtocolDriver.objects.update_or_create(
                handover=handover,
                defaults={
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "address": " ".join(
                        part
                        for part in (
                            customer.street,
                            customer.postal_code,
                            customer.city,
                        )
                        if part
                    ).strip(),
                },
            )
        if created or not handover.equipment_lines.exists():
            HandoverService._seed_equipment_lines(handover)
        if created or not handover.damage_markers.exists():
            HandoverService._seed_damage_markers_from_fleet(handover)
        return handover

    @staticmethod
    def _seed_equipment_lines(handover: HandoverProtocol) -> None:
        car = handover.rental.reservation.car
        for line in CarEquipment.objects.filter(car=car).select_related("item"):
            ProtocolEquipmentLine.objects.get_or_create(
                handover=handover,
                equipment_item=line.item,
                defaults={
                    "name_snapshot": line.item.name,
                    "quantity_expected": line.quantity,
                    "status": EquipmentLineStatus.PENDING,
                },
            )
        # Dodatki z rezerwacji (np. fotelik) — jesli maja odpowiednik w katalogu.
        reservation = handover.rental.reservation
        for price_line in reservation.price_lines.filter(line_type="extra"):
            code = (price_line.source_code or "").strip()
            if not code:
                continue
            from apps.fleet.models import EquipmentItem

            item = EquipmentItem.objects.filter(code=code, is_active=True).first()
            if item is None:
                continue
            ProtocolEquipmentLine.objects.get_or_create(
                handover=handover,
                equipment_item=item,
                defaults={
                    "name_snapshot": item.name,
                    "quantity_expected": 1,
                    "status": EquipmentLineStatus.PENDING,
                },
            )

    @staticmethod
    def _seed_damage_markers_from_fleet(handover: HandoverProtocol) -> None:
        from apps.fleet.models import Damage, DamageStatus

        car = handover.rental.reservation.car
        for damage in Damage.objects.filter(car=car, status=DamageStatus.ACTIVE):
            if damage.pos_x is None or damage.pos_y is None:
                continue
            ProtocolDamageMarker.objects.get_or_create(
                handover=handover,
                source_damage=damage,
                defaults={
                    "damage_type": damage.damage_type,
                    "description": damage.description,
                    "pos_x": damage.pos_x,
                    "pos_y": damage.pos_y,
                    "is_new": False,
                    "resolution": DamageMarkerResolution.ACTIVE,
                },
            )

    @staticmethod
    @transaction.atomic
    def save_driver(
        handover: HandoverProtocol,
        *,
        data: dict,
    ) -> ProtocolDriver:
        HandoverService._ensure_editable(handover)
        driver, _ = ProtocolDriver.objects.update_or_create(
            handover=handover,
            defaults={
                "first_name": data.get("first_name", "").strip(),
                "last_name": data.get("last_name", "").strip(),
                "email": data.get("email", "").strip(),
                "phone": data.get("phone", "").strip(),
                "address": data.get("address", "").strip(),
                "date_of_birth": data.get("date_of_birth") or None,
                "id_document_type": data.get("id_document_type", "").strip(),
                "id_document_number": data.get("id_document_number", "").strip(),
                "id_document_country": data.get("id_document_country", "").strip(),
                "license_number": data.get("license_number", "").strip(),
                "license_country": data.get("license_country", "").strip(),
                "license_issued_at": data.get("license_issued_at") or None,
                "license_expires_at": data.get("license_expires_at") or None,
                "document_verified": bool(data.get("document_verified")),
                "license_valid": bool(data.get("license_valid")),
                "license_category_ok": bool(data.get("license_category_ok")),
            },
        )
        handover.current_step = "odometer"
        handover.save(update_fields=["current_step", "updated_at"])
        return driver

    @staticmethod
    @transaction.atomic
    def save_odometer(
        handover: HandoverProtocol,
        *,
        mileage: int,
        fuel_level: str = "",
        fuel_level_percent: int | None = None,
        notes: str | None = None,
    ) -> HandoverProtocol:
        HandoverService._ensure_editable(handover)
        car_mileage = handover.rental.reservation.car.mileage
        if mileage < car_mileage:
            raise ValidationError(
                f"Przebieg ({mileage}) nie moze byc nizszy niz w bazie "
                f"({car_mileage} km)."
            )
        handover.mileage = mileage
        if fuel_level:
            handover.fuel_level = fuel_level
            handover.sync_fuel_percent()
        elif fuel_level_percent is not None:
            handover.fuel_level_percent = fuel_level_percent
            # Przyblizona skala do UI — nie nadpisuj dokladnego procentu.
            if not handover.fuel_level:
                handover.fuel_level = percent_to_fuel_level(fuel_level_percent)
        if notes is not None:
            handover.notes = notes
        handover.current_step = "damages"
        handover.save()
        return handover

    @staticmethod
    @transaction.atomic
    def add_damage_marker(
        handover: HandoverProtocol,
        *,
        damage_type: str,
        description: str,
        pos_x: Decimal,
        pos_y: Decimal,
        size_note: str = "",
        photo=None,
    ) -> ProtocolDamageMarker:
        HandoverService._ensure_editable(handover)
        marker = ProtocolDamageMarker.objects.create(
            handover=handover,
            damage_type=damage_type or DamageType.OTHER,
            description=description.strip(),
            size_note=size_note.strip(),
            pos_x=pos_x,
            pos_y=pos_y,
            is_new=True,
            resolution=DamageMarkerResolution.ACTIVE,
        )
        if photo:
            validate_image_upload(photo)
            ProtocolPhoto.objects.create(
                handover=handover,
                damage_marker=marker,
                category=ProtocolPhotoCategory.DETAIL,
                image=photo,
            )
        return marker

    @staticmethod
    @transaction.atomic
    def resolve_damage_marker(
        handover: HandoverProtocol,
        marker_id: int,
        *,
        resolution: str,
    ) -> ProtocolDamageMarker:
        HandoverService._ensure_editable(handover)
        marker = handover.damage_markers.filter(pk=marker_id).first()
        if marker is None:
            raise ValidationError("Nie znaleziono markera uszkodzenia.")
        marker.resolution = resolution
        marker.save(update_fields=["resolution", "updated_at"])
        return marker

    @staticmethod
    @transaction.atomic
    def add_photo(
        handover: HandoverProtocol,
        *,
        image,
        category: str = ProtocolPhotoCategory.OTHER,
        caption: str = "",
    ) -> ProtocolPhoto:
        HandoverService._ensure_editable(handover)
        validate_image_upload(image)
        return ProtocolPhoto.objects.create(
            handover=handover,
            image=image,
            category=category,
            caption=caption,
        )

    @staticmethod
    @transaction.atomic
    def save_interior(
        handover: HandoverProtocol,
        *,
        interior_notes: dict,
        inspection_notes: dict,
    ) -> HandoverProtocol:
        HandoverService._ensure_editable(handover)
        handover.interior_notes = interior_notes or {}
        handover.inspection_notes = inspection_notes or {}
        handover.current_step = "equipment"
        handover.save(
            update_fields=[
                "interior_notes",
                "inspection_notes",
                "current_step",
                "updated_at",
            ]
        )
        return handover

    @staticmethod
    @transaction.atomic
    def save_equipment(
        handover: HandoverProtocol,
        *,
        lines: list[dict],
        confirm_all: bool = False,
    ) -> HandoverProtocol:
        HandoverService._ensure_editable(handover)
        if confirm_all:
            for line in handover.equipment_lines.all():
                line.status = EquipmentLineStatus.HANDED
                line.quantity_actual = line.quantity_expected
                line.save(update_fields=["status", "quantity_actual"])
        for item in lines:
            line = handover.equipment_lines.filter(pk=item.get("id")).first()
            if line is None:
                continue
            line.status = item.get("status", line.status)
            if "quantity_actual" in item and item["quantity_actual"] is not None:
                line.quantity_actual = int(item["quantity_actual"])
            if "notes" in item:
                line.notes = str(item["notes"])
            line.save()
        handover.current_step = "summary"
        handover.status = ProtocolStatus.READY_FOR_SIGNATURE
        handover.save(update_fields=["current_step", "status", "updated_at"])
        return handover

    @staticmethod
    @transaction.atomic
    def finalize_handover(
        handover: HandoverProtocol,
        *,
        signer_name: str,
        signature_image,
        customer_notes: str = "",
        performed_by_id: int | None = None,
    ) -> HandoverProtocol:
        HandoverService._ensure_editable(handover)
        if handover.mileage is None:
            raise ValidationError("Uzupelnij przebieg przed podpisem.")
        if not handover.fuel_level and handover.fuel_level_percent is None:
            raise ValidationError("Uzupelnij poziom paliwa przed podpisem.")
        if not signer_name.strip():
            raise ValidationError("Podaj imie i nazwisko klienta podpisujacego.")
        if not signature_image:
            raise ValidationError("Wymagany podpis (zdjecie lub plik).")
        validate_image_upload(signature_image)

        # Zamroz snapshoty (raz).
        if not handover.damage_snapshots.exists():
            DamageSnapshotService.freeze_active_damages_for_handover(handover)
            car: Car = handover.rental.reservation.car
            for marker in handover.damage_markers.filter(
                is_new=True,
                resolution=DamageMarkerResolution.ACTIVE,
            ):
                damage = DamageService.report_damage(
                    car=car,
                    description=marker.description or marker.get_damage_type_display(),
                    location="",
                    severity="minor",
                    damage_type=marker.damage_type,
                    pos_x=marker.pos_x,
                    pos_y=marker.pos_y,
                )
                marker.source_damage = damage
                marker.save(update_fields=["source_damage"])
                DamageSnapshotService.snapshot_new_damage(
                    handover=handover,
                    damage=damage,
                )

        Signature.objects.update_or_create(
            handover=handover,
            defaults={
                "signer_name": signer_name.strip(),
                "image": signature_image,
                "customer_notes": customer_notes,
                "outcome": SignatureOutcome.SIGNED,
            },
        )

        handover.sync_fuel_percent()
        # Zachowaj fuel_level_percent jesli byl ustawiony dokladniej niz skala.
        handover.status = ProtocolStatus.COMPLETED
        handover.current_step = "signature"
        handover.completed_at = timezone.now()
        handover.completed_by_id = performed_by_id
        handover.save()

        car = handover.rental.reservation.car
        car.mileage = handover.mileage
        car.save(update_fields=["mileage"])

        rental = handover.rental
        if rental.status == RentalStatus.SCHEDULED:
            RentalService.start(rental, at=handover.completed_at)

        DocumentService.generate_handover_pdf(
            handover.pk,
            generated_by_id=performed_by_id,
        )
        AuditService.log(
            AuditAction.HANDOVER_COMPLETED,
            actor_id=performed_by_id,
            rental_id=rental.pk,
            reservation_id=rental.reservation_id,
            object_type="handover_protocol",
            object_id=handover.pk,
            metadata={
                "mileage": handover.mileage,
                "fuel_level": handover.fuel_level,
                "fuel_level_percent": handover.fuel_level_percent,
            },
        )
        return handover

    @staticmethod
    @transaction.atomic
    def complete_handover(
        rental_id: int,
        *,
        mileage: int,
        fuel_level_percent: int,
        signer_name: str,
        signature_image,
        notes: str = "",
        photo_files: list | None = None,
        new_damages: list[dict] | None = None,
        performed_by_id: int | None = None,
        fuel_level: str = "",
    ) -> HandoverProtocol:
        """Facade kompatybilna z MVP — jeden request = pelny cykl."""
        handover = HandoverService.start_handover(rental_id)
        HandoverService.save_odometer(
            handover,
            mileage=mileage,
            fuel_level=fuel_level,
            fuel_level_percent=fuel_level_percent,
            notes=notes,
        )
        validate_image_uploads(photo_files or [])
        for image in photo_files or []:
            if image:
                HandoverService.add_photo(handover, image=image)

        car: Car = handover.rental.reservation.car
        for item in new_damages or []:
            damage = DamageService.report_damage(
                car=car,
                description=item.get("description", "").strip(),
                location=item.get("location", "").strip(),
                severity=item.get("severity", "minor"),
                damage_type=item.get("damage_type", DamageType.OTHER),
                pos_x=item.get("pos_x"),
                pos_y=item.get("pos_y"),
            )
            ProtocolDamageMarker.objects.create(
                handover=handover,
                source_damage=damage,
                damage_type=damage.damage_type,
                description=damage.description,
                pos_x=damage.pos_x or Decimal("50"),
                pos_y=damage.pos_y or Decimal("50"),
                is_new=True,
            )

        handover.equipment_lines.update(status=EquipmentLineStatus.HANDED)
        for line in handover.equipment_lines.all():
            line.quantity_actual = line.quantity_expected
            line.status = EquipmentLineStatus.HANDED
            line.save(update_fields=["quantity_actual", "status"])

        return HandoverService.finalize_handover(
            handover,
            signer_name=signer_name,
            signature_image=signature_image,
            performed_by_id=performed_by_id,
        )
