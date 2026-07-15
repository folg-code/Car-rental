from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services.audit import AuditService
from apps.bookings.models import Rental, RentalStatus
from apps.bookings.services.rental import RentalService
from apps.documents.services.document import DocumentService
from apps.fleet.models import Car
from apps.fleet.services.damage import DamageService
from apps.operations.models import HandoverProtocol, ProtocolPhoto, Signature
from apps.operations.services.damage_snapshot import DamageSnapshotService
from config.upload_validation import validate_image_upload, validate_image_uploads


class HandoverService:
    @staticmethod
    def _get_rental_for_handover(rental_id: int) -> Rental:
        rental = (
            Rental.objects.select_related("reservation", "reservation__car")
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
                .only("completed_at")
                .first()
            )
            if handover is None or not handover.is_completed:
                return rental
        raise ValidationError(
            "Protokol wydania mozna zlozyc tylko dla wynajmu zaplanowanego "
            "lub aktywnego bez zakonczonego protokolu."
        )

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
    ) -> HandoverProtocol:
        rental = HandoverService._get_rental_for_handover(rental_id)
        if hasattr(rental, "handover_protocol"):
            existing = rental.handover_protocol
            if existing.is_completed:
                raise ValidationError("Protokol wydania jest juz zakonczony.")

        if mileage < rental.reservation.car.mileage:
            raise ValidationError(
                f"Przebieg ({mileage}) nie moze byc nizszy niz w bazie "
                f"({rental.reservation.car.mileage} km)."
            )

        handover, _ = HandoverProtocol.objects.update_or_create(
            rental=rental,
            defaults={
                "mileage": mileage,
                "fuel_level_percent": fuel_level_percent,
                "notes": notes,
            },
        )

        DamageSnapshotService.freeze_active_damages_for_handover(handover)

        car: Car = rental.reservation.car
        for item in new_damages or []:
            damage = DamageService.report_damage(
                car=car,
                description=item.get("description", "").strip(),
                location=item.get("location", "").strip(),
                severity=item.get("severity", "minor"),
            )
            DamageSnapshotService.snapshot_new_damage(
                handover=handover,
                damage=damage,
            )

        validate_image_uploads(photo_files or [])

        for image in photo_files or []:
            if image:
                ProtocolPhoto.objects.create(handover=handover, image=image)

        if not signer_name.strip():
            raise ValidationError("Podaj imie i nazwisko klienta podpisujacego.")
        if not signature_image:
            raise ValidationError("Wymagany podpis (zdjecie lub plik).")
        validate_image_upload(signature_image)

        Signature.objects.update_or_create(
            handover=handover,
            defaults={
                "signer_name": signer_name.strip(),
                "image": signature_image,
            },
        )

        handover.completed_at = timezone.now()
        handover.completed_by_id = performed_by_id
        handover.save(
            update_fields=[
                "mileage",
                "fuel_level_percent",
                "notes",
                "completed_at",
                "completed_by",
                "updated_at",
            ]
        )

        car.mileage = mileage
        car.save(update_fields=["mileage"])

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
                "fuel_level_percent": handover.fuel_level_percent,
            },
        )
        return handover
