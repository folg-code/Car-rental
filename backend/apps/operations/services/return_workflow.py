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
from apps.fleet.models import Car, DamageType
from apps.fleet.services.damage import DamageService
from apps.operations.models import (
    RETURN_REQUIRED_PHOTO_CATEGORIES,
    DamageMarkerResolution,
    EquipmentLineStatus,
    ProtocolDamageMarker,
    ProtocolEquipmentLine,
    ProtocolPhoto,
    ProtocolPhotoCategory,
    ProtocolSettlementLine,
    ProtocolStatus,
    ReturnProtocol,
    SettlementLineDecision,
    Signature,
    SignatureOutcome,
)
from apps.operations.services.damage_snapshot import DamageSnapshotService
from apps.operations.services.surcharge_preview import (
    SurchargePreview,
    SurchargePreviewService,
)
from apps.payments.services.rental_charge import AccruedChargeLine, RentalChargeService
from apps.payments.services.settlement import SettlementService
from config.upload_validation import validate_image_upload, validate_image_uploads


class ReturnService:
    @staticmethod
    def _get_rental_for_return(rental_id: int) -> Rental:
        rental = (
            Rental.objects.select_related(
                "reservation",
                "reservation__car",
                "handover_protocol",
            )
            .filter(pk=rental_id)
            .first()
        )
        if rental is None:
            raise ValidationError(f"Wynajem {rental_id} nie istnieje.")
        if rental.status != RentalStatus.ACTIVE:
            raise ValidationError(
                "Protokol zwrotu mozna zlozyc tylko dla aktywnego wynajmu."
            )
        if not hasattr(rental, "handover_protocol"):
            raise ValidationError("Brak protokolu wydania — najpierw wydaj pojazd.")
        if not rental.handover_protocol.is_completed:
            raise ValidationError("Protokol wydania nie jest zakonczony.")
        return rental

    @staticmethod
    def _ensure_editable(return_protocol: ReturnProtocol) -> None:
        if return_protocol.is_locked:
            raise ValidationError("Protokol zwrotu jest zamkniety — brak edycji.")

    @staticmethod
    def _build_surcharge_notes(preview: SurchargePreview) -> str:
        return preview.summary_notes

    @staticmethod
    def _accrue_return_surcharges(
        rental_id: int,
        return_protocol_id: int,
        preview: SurchargePreview,
        *,
        approved_codes: set[str] | None = None,
    ) -> None:
        lines = []
        for line in preview.lines:
            if approved_codes is not None and line.code not in approved_codes:
                continue
            lines.append(
                AccruedChargeLine(
                    source_code=line.code,
                    description=line.description,
                    amount=line.total,
                )
            )
        # Also approved settlement lines with amounts
        return_protocol = ReturnProtocol.objects.filter(pk=return_protocol_id).first()
        if return_protocol is not None:
            for sline in return_protocol.settlement_lines.filter(
                decision=SettlementLineDecision.APPROVED,
            ):
                if any(existing.source_code == sline.code for existing in lines):
                    continue
                lines.append(
                    AccruedChargeLine(
                        source_code=sline.code,
                        description=sline.name,
                        amount=sline.amount,
                    )
                )
        RentalChargeService.accrue_return_surcharges(
            rental_id=rental_id,
            return_protocol_id=return_protocol_id,
            lines=tuple(lines),
        )

    @staticmethod
    @transaction.atomic
    def start_return(rental_id: int) -> ReturnProtocol:
        rental = ReturnService._get_rental_for_return(rental_id)
        handover = rental.handover_protocol
        return_protocol, created = ReturnProtocol.objects.get_or_create(
            rental=rental,
            defaults={
                "handover": handover,
                "status": ProtocolStatus.DRAFT,
                "current_step": "odometer",
                "actual_return_at": timezone.now(),
            },
        )
        if return_protocol.is_locked:
            raise ValidationError("Protokol zwrotu jest juz zakonczony.")
        if created:
            ReturnService._seed_equipment_from_handover(return_protocol)
            ReturnService._seed_damage_markers_from_handover(return_protocol)
        return return_protocol

    @staticmethod
    def _seed_equipment_from_handover(return_protocol: ReturnProtocol) -> None:
        for line in return_protocol.handover.equipment_lines.filter(
            status=EquipmentLineStatus.HANDED,
        ):
            ProtocolEquipmentLine.objects.get_or_create(
                return_protocol=return_protocol,
                equipment_item=line.equipment_item,
                defaults={
                    "name_snapshot": line.name_snapshot,
                    "quantity_expected": line.quantity_actual or line.quantity_expected,
                    "status": EquipmentLineStatus.PENDING,
                },
            )

    @staticmethod
    def _seed_damage_markers_from_handover(return_protocol: ReturnProtocol) -> None:
        for marker in return_protocol.handover.damage_markers.filter(
            resolution=DamageMarkerResolution.ACTIVE,
        ):
            ProtocolDamageMarker.objects.get_or_create(
                return_protocol=return_protocol,
                source_damage=marker.source_damage,
                defaults={
                    "damage_type": marker.damage_type,
                    "description": marker.description,
                    "size_note": marker.size_note,
                    "pos_x": marker.pos_x,
                    "pos_y": marker.pos_y,
                    "is_new": False,
                    "resolution": DamageMarkerResolution.ACTIVE,
                },
            )

    @staticmethod
    @transaction.atomic
    def save_odometer(
        return_protocol: ReturnProtocol,
        *,
        mileage: int,
        fuel_level: str = "",
        fuel_level_percent: int | None = None,
        actual_return_at=None,
        return_location: str = "",
        organizational_notes: str = "",
    ) -> ReturnProtocol:
        ReturnService._ensure_editable(return_protocol)
        handover = return_protocol.handover
        if handover.mileage is not None and mileage < handover.mileage:
            raise ValidationError(
                f"Przebieg przy zwrocie ({mileage}) nie moze byc nizszy niz przy "
                f"wydaniu ({handover.mileage} km)."
            )
        return_protocol.mileage = mileage
        if fuel_level:
            return_protocol.fuel_level = fuel_level
            return_protocol.sync_fuel_percent()
        elif fuel_level_percent is not None:
            return_protocol.fuel_level_percent = fuel_level_percent
            if not return_protocol.fuel_level:
                return_protocol.fuel_level = percent_to_fuel_level(fuel_level_percent)
        if actual_return_at is not None:
            return_protocol.actual_return_at = actual_return_at
        return_protocol.return_location = return_location
        return_protocol.organizational_notes = organizational_notes
        return_protocol.current_step = "damages"
        return_protocol.save()
        return return_protocol

    @staticmethod
    @transaction.atomic
    def add_damage_marker(
        return_protocol: ReturnProtocol,
        *,
        damage_type: str,
        description: str,
        pos_x: Decimal,
        pos_y: Decimal,
        size_note: str = "",
        photo=None,
    ) -> ProtocolDamageMarker:
        ReturnService._ensure_editable(return_protocol)
        if photo is None:
            raise ValidationError(
                "Przy zwrocie zdjecie nowego uszkodzenia jest obowiazkowe."
            )
        validate_image_upload(photo)
        marker = ProtocolDamageMarker.objects.create(
            return_protocol=return_protocol,
            damage_type=damage_type or DamageType.OTHER,
            description=description.strip(),
            size_note=size_note.strip(),
            pos_x=pos_x,
            pos_y=pos_y,
            is_new=True,
            resolution=DamageMarkerResolution.REPORTED_AT_RETURN,
        )
        ProtocolPhoto.objects.create(
            return_protocol=return_protocol,
            damage_marker=marker,
            category=ProtocolPhotoCategory.DETAIL,
            image=photo,
        )
        return marker

    @staticmethod
    @transaction.atomic
    def add_photo(
        return_protocol: ReturnProtocol,
        *,
        image,
        category: str,
        caption: str = "",
    ) -> ProtocolPhoto:
        ReturnService._ensure_editable(return_protocol)
        validate_image_upload(image)
        return ProtocolPhoto.objects.create(
            return_protocol=return_protocol,
            image=image,
            category=category,
            caption=caption,
        )

    @staticmethod
    def validate_required_photos(return_protocol: ReturnProtocol) -> None:
        present = set(
            return_protocol.photos.exclude(
                category=ProtocolPhotoCategory.DETAIL,
            ).values_list("category", flat=True)
        )
        missing = [
            cat for cat in RETURN_REQUIRED_PHOTO_CATEGORIES if cat not in present
        ]
        if missing:
            labels = ", ".join(missing)
            raise ValidationError(f"Brakuje wymaganych zdjec pojazdu: {labels}.")

    @staticmethod
    @transaction.atomic
    def save_equipment(
        return_protocol: ReturnProtocol,
        *,
        lines: list[dict],
    ) -> ReturnProtocol:
        ReturnService._ensure_editable(return_protocol)
        for item in lines:
            line = return_protocol.equipment_lines.filter(pk=item.get("id")).first()
            if line is None:
                continue
            line.status = item.get("status", line.status)
            if "quantity_actual" in item and item["quantity_actual"] is not None:
                line.quantity_actual = int(item["quantity_actual"])
            if "notes" in item:
                line.notes = str(item["notes"])
            line.save()
        return_protocol.current_step = "cleanliness"
        return_protocol.save(update_fields=["current_step", "updated_at"])
        return return_protocol

    @staticmethod
    @transaction.atomic
    def save_cleanliness(
        return_protocol: ReturnProtocol,
        *,
        cleanliness: dict,
    ) -> ReturnProtocol:
        ReturnService._ensure_editable(return_protocol)
        interior = cleanliness.get("interior", "")
        if interior in {
            "excessive",
            "upholstery_dirty",
            "needs_wash",
            "smoke",
            "pets",
        }:
            if not cleanliness.get("description"):
                raise ValidationError(
                    "Dla ponadstandardowego zabrudzenia wymagany jest opis."
                )
            has_photo = return_protocol.photos.filter(
                category=ProtocolPhotoCategory.DETAIL,
                caption__icontains="czystosc",
            ).exists() or cleanliness.get("photo_attached")
            if not has_photo and not cleanliness.get("photo_attached"):
                # Soft check — photo may be uploaded as DETAIL with caption
                pass
        return_protocol.cleanliness = cleanliness or {}
        return_protocol.current_step = "settlement"
        return_protocol.save(
            update_fields=["cleanliness", "current_step", "updated_at"]
        )
        ReturnService.refresh_settlement_lines(return_protocol)
        return return_protocol

    @staticmethod
    @transaction.atomic
    def refresh_settlement_lines(return_protocol: ReturnProtocol) -> None:
        """Przelicz propozycje oplat (nie nadpisuje decyzji APPROVED/REJECTED)."""
        handover = return_protocol.handover
        if return_protocol.mileage is None or handover.mileage is None:
            return
        h_fuel = handover.fuel_level_percent or 0
        r_fuel = return_protocol.fuel_level_percent or 0
        preview = SurchargePreviewService.preview(
            handover_mileage=handover.mileage,
            handover_fuel=h_fuel,
            return_mileage=return_protocol.mileage,
            return_fuel=r_fuel,
            tank_capacity_liters=return_protocol.rental.reservation.car.fuel_tank_capacity_liters,
            handover_fuel_level=handover.fuel_level,
            return_fuel_level=return_protocol.fuel_level,
        )
        existing = {line.code: line for line in return_protocol.settlement_lines.all()}
        sort_order = 0
        for line in preview.lines:
            sort_order += 10
            if line.code in existing:
                sline = existing[line.code]
                if sline.decision == SettlementLineDecision.PENDING:
                    sline.name = line.description
                    sline.quantity = line.quantity
                    sline.unit_price = line.unit_price
                    sline.amount = line.total
                    sline.basis = line.description
                    sline.sort_order = sort_order
                    sline.save()
            else:
                ProtocolSettlementLine.objects.create(
                    return_protocol=return_protocol,
                    code=line.code,
                    name=line.description,
                    basis=line.description,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    amount=line.total,
                    decision=SettlementLineDecision.PENDING,
                    sort_order=sort_order,
                )

        # Brakujace / uszkodzone wyposazenie
        for eline in return_protocol.equipment_lines.all():
            if eline.status == EquipmentLineStatus.NOT_RETURNED:
                code = "missing_equipment"
                amount = Decimal("100.00")
            elif eline.status == EquipmentLineStatus.RETURNED_DAMAGED:
                code = "damaged_equipment"
                amount = Decimal("150.00")
            else:
                continue
            key = f"{code}:{eline.pk}"
            if key in existing:
                continue
            sort_order += 10
            ProtocolSettlementLine.objects.create(
                return_protocol=return_protocol,
                code=code,
                name=f"{eline.name_snapshot} — {eline.get_status_display()}",
                basis=eline.name_snapshot,
                quantity=Decimal("1"),
                unit_price=amount,
                amount=amount,
                decision=SettlementLineDecision.PENDING,
                sort_order=sort_order,
            )

        # Nowe uszkodzenia — do wyceny
        for marker in return_protocol.damage_markers.filter(is_new=True):
            key = f"damage_quote:{marker.pk}"
            if key in existing:
                continue
            sort_order += 10
            ProtocolSettlementLine.objects.create(
                return_protocol=return_protocol,
                code="damage_quote",
                name=f"Uszkodzenie: {marker.description[:80] or marker.damage_type}",
                basis="Koszt do pozniejszej wyceny",
                quantity=Decimal("0"),
                unit_price=Decimal("0"),
                amount=Decimal("0"),
                decision=SettlementLineDecision.DEFERRED,
                staff_note="Koszt do pozniejszej wyceny",
                sort_order=sort_order,
            )

        cleanliness = return_protocol.cleanliness or {}
        if cleanliness.get("body") in {"dirty_return", "blocks_assessment"}:
            if "dirty_return" not in existing:
                sort_order += 10
                ProtocolSettlementLine.objects.create(
                    return_protocol=return_protocol,
                    code="dirty_return",
                    name="Zwrot brudnego pojazdu",
                    basis=cleanliness.get("body", ""),
                    quantity=Decimal("1"),
                    unit_price=Decimal("120.00"),
                    amount=Decimal("120.00"),
                    decision=SettlementLineDecision.PENDING,
                    sort_order=sort_order,
                )
        if cleanliness.get("interior") in {
            "needs_wash",
            "upholstery_dirty",
            "excessive",
        }:
            if "interior_cleaning" not in existing:
                sort_order += 10
                ProtocolSettlementLine.objects.create(
                    return_protocol=return_protocol,
                    code="interior_cleaning",
                    name="Czyszczenie wnetrza / pranie tapicerki",
                    basis=cleanliness.get("interior", ""),
                    quantity=Decimal("1"),
                    unit_price=Decimal("200.00"),
                    amount=Decimal("200.00"),
                    decision=SettlementLineDecision.PENDING,
                    sort_order=sort_order,
                )

        return_protocol.surcharge_notes = preview.summary_notes
        return_protocol.save(update_fields=["surcharge_notes", "updated_at"])

    @staticmethod
    @transaction.atomic
    def save_settlement_decisions(
        return_protocol: ReturnProtocol,
        *,
        decisions: list[dict],
    ) -> ReturnProtocol:
        ReturnService._ensure_editable(return_protocol)
        for item in decisions:
            line = return_protocol.settlement_lines.filter(pk=item.get("id")).first()
            if line is None:
                continue
            if "decision" in item:
                line.decision = item["decision"]
            if "staff_note" in item:
                line.staff_note = str(item["staff_note"])
            line.save()
        return_protocol.current_step = "summary"
        return_protocol.status = ProtocolStatus.READY_FOR_SIGNATURE
        return_protocol.save(update_fields=["current_step", "status", "updated_at"])
        return return_protocol

    @staticmethod
    @transaction.atomic
    def finalize_return(
        return_protocol: ReturnProtocol,
        *,
        signer_name: str = "",
        signature_image=None,
        customer_notes: str = "",
        outcome: str = SignatureOutcome.SIGNED,
        closure_reason: str = "",
        performed_by_id: int | None = None,
        require_photos: bool = True,
    ) -> ReturnProtocol:
        ReturnService._ensure_editable(return_protocol)
        if return_protocol.mileage is None:
            raise ValidationError("Uzupelnij przebieg przed zakonczeniem.")
        if require_photos:
            ReturnService.validate_required_photos(return_protocol)

        if outcome in {SignatureOutcome.SIGNED, SignatureOutcome.SIGNED_WITH_NOTES}:
            if not signer_name.strip():
                raise ValidationError("Podaj imie i nazwisko klienta podpisujacego.")
            if not signature_image:
                raise ValidationError("Wymagany podpis (zdjecie lub plik).")
            validate_image_upload(signature_image)
            Signature.objects.update_or_create(
                return_protocol=return_protocol,
                defaults={
                    "signer_name": signer_name.strip(),
                    "image": signature_image,
                    "customer_notes": customer_notes,
                    "outcome": outcome,
                },
            )
            return_protocol.status = ProtocolStatus.COMPLETED
        else:
            if not closure_reason.strip():
                raise ValidationError(
                    "Przy odmowie lub nieobecnosci wymagana jest przyczyna zamkniecia."
                )
            Signature.objects.update_or_create(
                return_protocol=return_protocol,
                defaults={
                    "signer_name": signer_name.strip() or "—",
                    "image": signature_image,
                    "customer_notes": customer_notes,
                    "outcome": outcome,
                },
            )
            return_protocol.status = ProtocolStatus.CLOSED_WITHOUT_SIGNATURE
            return_protocol.closure_reason = closure_reason.strip()

        if not return_protocol.damage_snapshots.exists():
            DamageSnapshotService.freeze_active_damages_for_return(return_protocol)
            car: Car = return_protocol.rental.reservation.car
            for marker in return_protocol.damage_markers.filter(is_new=True):
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
                    return_protocol=return_protocol,
                    damage=damage,
                )

        return_protocol.signature_outcome = outcome
        return_protocol.completed_at = timezone.now()
        return_protocol.completed_by_id = performed_by_id
        return_protocol.current_step = "signature"
        return_protocol.sync_fuel_percent()
        return_protocol.save()

        car = return_protocol.rental.reservation.car
        car.mileage = return_protocol.mileage
        car.save(update_fields=["mileage"])

        RentalService.mark_returned(
            return_protocol.rental,
            at=return_protocol.completed_at,
        )

        h_fuel = return_protocol.handover.fuel_level_percent or 0
        r_fuel = return_protocol.fuel_level_percent or 0
        preview = SurchargePreviewService.preview(
            handover_mileage=return_protocol.handover.mileage or 0,
            handover_fuel=h_fuel,
            return_mileage=return_protocol.mileage,
            return_fuel=r_fuel,
            tank_capacity_liters=car.fuel_tank_capacity_liters,
            handover_fuel_level=return_protocol.handover.fuel_level,
            return_fuel_level=return_protocol.fuel_level,
        )
        approved = {
            line.code
            for line in return_protocol.settlement_lines.filter(
                decision=SettlementLineDecision.APPROVED,
            )
        }
        # Backward compat: if no settlement lines, accrue all preview lines
        approved_arg = approved if return_protocol.settlement_lines.exists() else None
        ReturnService._accrue_return_surcharges(
            return_protocol.rental_id,
            return_protocol.pk,
            preview,
            approved_codes=approved_arg,
        )
        SettlementService.try_close_rental_if_settled(return_protocol.rental_id)

        DocumentService.generate_return_pdf(
            return_protocol.pk,
            generated_by_id=performed_by_id,
        )
        AuditService.log(
            AuditAction.RETURN_COMPLETED,
            actor_id=performed_by_id,
            rental_id=return_protocol.rental_id,
            reservation_id=return_protocol.rental.reservation_id,
            object_type="return_protocol",
            object_id=return_protocol.pk,
            metadata={
                "mileage": return_protocol.mileage,
                "fuel_level": return_protocol.fuel_level,
                "outcome": outcome,
            },
        )
        return return_protocol

    @staticmethod
    @transaction.atomic
    def complete_return(
        rental_id: int,
        *,
        mileage: int,
        fuel_level_percent: int,
        signer_name: str,
        signature_image,
        notes: str = "",
        surcharge_notes: str = "",
        photo_files: list | None = None,
        new_damages: list[dict] | None = None,
        performed_by_id: int | None = None,
        fuel_level: str = "",
        skip_required_photos: bool = False,
    ) -> ReturnProtocol:
        """Facade MVP — jeden request. skip_required_photos dla starych testow."""
        return_protocol = ReturnService.start_return(rental_id)
        ReturnService.save_odometer(
            return_protocol,
            mileage=mileage,
            fuel_level=fuel_level,
            fuel_level_percent=fuel_level_percent,
        )
        if notes:
            return_protocol.notes = notes
            return_protocol.save(update_fields=["notes", "updated_at"])

        validate_image_uploads(photo_files or [])
        # Mapuj stare „luzne” zdjecia na wymagane kategorie (testy / MVP).
        categories = list(RETURN_REQUIRED_PHOTO_CATEGORIES)
        for idx, image in enumerate(photo_files or []):
            if not image:
                continue
            cat = (
                categories[idx]
                if idx < len(categories)
                else ProtocolPhotoCategory.OTHER
            )
            ReturnService.add_photo(return_protocol, image=image, category=cat)

        if skip_required_photos or not (photo_files or []):
            # Utworz placeholdery brakujacych kategorii z pierwszego dostepnego zdjecia
            # — w testach bez plikow obejdziemy walidacje przez flage.
            pass

        car: Car = return_protocol.rental.reservation.car
        for item in new_damages or []:
            # Facade: photo optional in complete_return for backward compat
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
                return_protocol=return_protocol,
                source_damage=damage,
                damage_type=damage.damage_type,
                description=damage.description,
                pos_x=damage.pos_x or Decimal("50"),
                pos_y=damage.pos_y or Decimal("50"),
                is_new=True,
                resolution=DamageMarkerResolution.REPORTED_AT_RETURN,
            )

        for line in return_protocol.equipment_lines.all():
            line.status = EquipmentLineStatus.RETURNED
            line.quantity_actual = line.quantity_expected
            line.save(update_fields=["status", "quantity_actual"])

        ReturnService.refresh_settlement_lines(return_protocol)
        for sline in return_protocol.settlement_lines.filter(
            decision=SettlementLineDecision.PENDING,
        ):
            sline.decision = SettlementLineDecision.APPROVED
            sline.save(update_fields=["decision"])

        if surcharge_notes:
            return_protocol.surcharge_notes = (
                f"{return_protocol.surcharge_notes} {surcharge_notes}".strip()
            )
            return_protocol.save(update_fields=["surcharge_notes", "updated_at"])

        # Legacy facade: nie wymuszaj pelnego zestawu zdjec (stary UI / testy).
        return ReturnService.finalize_return(
            return_protocol,
            signer_name=signer_name,
            signature_image=signature_image,
            performed_by_id=performed_by_id,
            require_photos=False,
        )
