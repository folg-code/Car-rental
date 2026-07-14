from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Rental, RentalStatus
from apps.bookings.services.rental import RentalService
from apps.documents.services.document import DocumentService
from apps.fleet.models import Car
from apps.fleet.services.damage import DamageService
from apps.operations.models import ProtocolPhoto, ReturnProtocol, Signature
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
    def _build_surcharge_notes(preview: SurchargePreview) -> str:
        return preview.summary_notes

    @staticmethod
    def _accrue_return_surcharges(
        rental_id: int,
        return_protocol_id: int,
        preview: SurchargePreview,
    ) -> None:
        lines = tuple(
            AccruedChargeLine(
                source_code=line.code,
                description=line.description,
                amount=line.total,
            )
            for line in preview.lines
        )
        RentalChargeService.accrue_return_surcharges(
            rental_id=rental_id,
            return_protocol_id=return_protocol_id,
            lines=lines,
        )

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
    ) -> ReturnProtocol:
        rental = ReturnService._get_rental_for_return(rental_id)
        handover = rental.handover_protocol

        if hasattr(rental, "return_protocol") and rental.return_protocol.is_completed:
            raise ValidationError("Protokol zwrotu jest juz zakonczony.")

        if mileage < handover.mileage:
            raise ValidationError(
                f"Przebieg przy zwrocie ({mileage}) nie moze byc nizszy niz przy "
                f"wydaniu ({handover.mileage} km)."
            )

        preview = SurchargePreviewService.preview(
            handover_mileage=handover.mileage,
            handover_fuel=handover.fuel_level_percent,
            return_mileage=mileage,
            return_fuel=fuel_level_percent,
        )
        auto_surcharge = ReturnService._build_surcharge_notes(preview)
        combined_surcharge = " ".join(
            part for part in (auto_surcharge, surcharge_notes.strip()) if part
        )

        return_protocol, _ = ReturnProtocol.objects.update_or_create(
            rental=rental,
            defaults={
                "handover": handover,
                "mileage": mileage,
                "fuel_level_percent": fuel_level_percent,
                "notes": notes,
                "surcharge_notes": combined_surcharge,
            },
        )

        DamageSnapshotService.freeze_active_damages_for_return(return_protocol)

        car: Car = rental.reservation.car
        for item in new_damages or []:
            damage = DamageService.report_damage(
                car=car,
                description=item.get("description", "").strip(),
                location=item.get("location", "").strip(),
                severity=item.get("severity", "minor"),
            )
            DamageSnapshotService.snapshot_new_damage(
                return_protocol=return_protocol,
                damage=damage,
            )

        validate_image_uploads(photo_files or [])

        for image in photo_files or []:
            if image:
                ProtocolPhoto.objects.create(
                    return_protocol=return_protocol,
                    image=image,
                )

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
            },
        )

        return_protocol.completed_at = timezone.now()
        return_protocol.completed_by_id = performed_by_id
        return_protocol.save(
            update_fields=[
                "handover",
                "mileage",
                "fuel_level_percent",
                "notes",
                "surcharge_notes",
                "completed_at",
                "completed_by",
                "updated_at",
            ]
        )

        car.mileage = mileage
        car.save(update_fields=["mileage"])

        RentalService.mark_returned(rental, at=return_protocol.completed_at)

        ReturnService._accrue_return_surcharges(
            rental.pk,
            return_protocol.pk,
            preview,
        )
        SettlementService.try_close_rental_if_settled(rental.pk)

        DocumentService.generate_return_pdf(
            return_protocol.pk,
            generated_by_id=performed_by_id,
        )
        return return_protocol
