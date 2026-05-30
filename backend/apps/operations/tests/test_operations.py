from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.models import Document, DocumentType, EmailStatus
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.fleet.services.damage import DamageService
from apps.operations.models import DamageSnapshot, HandoverProtocol
from apps.operations.services.damage_snapshot import DamageSnapshotService
from apps.operations.services.handover import HandoverService
from apps.operations.services.return_workflow import ReturnService
from apps.pricing.models import DailyRate, PriceList


def _tiny_image(name: str = "sig.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        b"\x89PNG\r\n\x1a\n",
        content_type="image/png",
    )


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV", slug="suv-ops", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Ops",
        slug="ops-test",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("100"))
    return pl


@pytest.fixture
def scheduled_rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@ops.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1OPS01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
    )
    start = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)


@pytest.mark.django_db
class TestDamageSnapshotImmutability:
    def test_snapshot_unchanged_after_fleet_damage_edit(self, scheduled_rental) -> None:
        car = scheduled_rental.reservation.car
        damage = DamageService.report_damage(
            car=car,
            description="Rysa na drzwiach",
            location="lewe przednie",
            severity="minor",
        )
        handover = HandoverProtocol.objects.create(
            rental=scheduled_rental,
            mileage=10_500,
            fuel_level_percent=80,
            completed_at=datetime(2026, 8, 1, 11, 0, tzinfo=UTC),
        )
        DamageSnapshotService.freeze_active_damages_for_handover(handover)
        snap = DamageSnapshot.objects.get(
            handover=handover,
            source_damage=damage,
        )
        original_desc = snap.description

        damage.description = "Rysa powazniejsza po edycji w flocie"
        damage.save(update_fields=["description"])

        snap.refresh_from_db()
        assert snap.description == original_desc
        assert snap.description != damage.description


@pytest.mark.django_db
class TestHandoverService:
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@test.car-rental.local",
    )
    def test_complete_handover_activates_rental(self, scheduled_rental) -> None:
        from apps.bookings.models import RentalStatus

        mail.outbox.clear()
        handover = HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_200,
            fuel_level_percent=90,
            signer_name="Jan Kowalski",
            signature_image=_tiny_image(),
        )
        scheduled_rental.refresh_from_db()
        assert handover.is_completed
        assert scheduled_rental.status == RentalStatus.ACTIVE
        assert scheduled_rental.reservation.car.mileage == 10_200

        pdf = Document.objects.filter(
            handover_protocol=handover,
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
        ).first()
        assert pdf is not None
        assert pdf.version == 1
        assert len(pdf.file_hash) == 64

        email_log = pdf.email_logs.filter(status=EmailStatus.SENT).first()
        assert email_log is not None
        assert email_log.recipient_email == "jan@ops.test"
        assert len(mail.outbox) == 1
        assert len(mail.outbox[0].attachments) == 1

    def test_handover_rejects_lower_mileage(self, scheduled_rental) -> None:
        with pytest.raises(ValidationError, match="Przebieg"):
            HandoverService.complete_handover(
                scheduled_rental.pk,
                mileage=5000,
                fuel_level_percent=50,
                signer_name="Jan",
                signature_image=_tiny_image(),
            )


@pytest.mark.django_db
class TestReturnService:
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@test.car-rental.local",
    )
    def test_complete_return_marks_rental_returned(self, scheduled_rental) -> None:
        from apps.bookings.models import RentalStatus

        mail.outbox.clear()
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )
        scheduled_rental.refresh_from_db()

        ret = ReturnService.complete_return(
            scheduled_rental.pk,
            mileage=10_350,
            fuel_level_percent=70,
            signer_name="Jan",
            signature_image=_tiny_image("ret.png"),
        )
        scheduled_rental.refresh_from_db()
        assert ret.is_completed
        assert scheduled_rental.status == RentalStatus.RETURNED
        assert "paliwa" in ret.surcharge_notes.lower() or ret.surcharge_notes

        pdf = Document.objects.filter(
            return_protocol=ret,
            document_type=DocumentType.RETURN_PROTOCOL_PDF,
        ).first()
        assert pdf is not None
        assert pdf.version == 1
        assert pdf.email_logs.filter(status=EmailStatus.SENT).exists()
        assert len(mail.outbox) == 2
        assert mail.outbox[-1].to == ["jan@ops.test"]
