"""
Sprint 7.10 — testy integracyjne documents + operations.

Pelny przeplyw: protokol → PDF → email;
integralnosc historyczna; awaria email bez rollbacku.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.bookings.models import Customer, RentalStatus, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.models import Document, DocumentType, EmailStatus
from apps.documents.services.invoice import InvoiceService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.fleet.services.damage import DamageService
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
        name="SUV", slug="suv-integration", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def locmem_email(settings) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@test.car-rental.local"


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Integration tests",
        slug="docs-integration",
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
        email="jan@integration.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1INT01",
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
class TestPdfImmutabilityIntegration:
    def test_handover_pdf_unchanged_after_fleet_damage_edit(
        self,
        scheduled_rental,
    ) -> None:
        car = scheduled_rental.reservation.car
        damage = DamageService.report_damage(
            car=car,
            description="Rysa na drzwiach",
            location="lewe przednie",
            severity="minor",
        )

        handover = HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_200,
            fuel_level_percent=90,
            signer_name="Jan Kowalski",
            signature_image=_tiny_image(),
        )
        doc = Document.objects.get(
            handover_protocol=handover,
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            version=1,
        )
        original_hash = doc.file_hash
        original_bytes = (settings.DOCUMENTS_PRIVATE_ROOT / doc.file.name).read_bytes()

        damage.description = "Rysa powazniejsza po edycji w flocie"
        damage.save(update_fields=["description"])

        doc.refresh_from_db()
        assert doc.file_hash == original_hash
        assert (
            settings.DOCUMENTS_PRIVATE_ROOT / doc.file.name
        ).read_bytes() == original_bytes

        snap = handover.damage_snapshots.get(source_damage=damage)
        assert snap.description != damage.description

    def test_return_pdf_unchanged_after_fleet_damage_edit(
        self,
        scheduled_rental,
    ) -> None:
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )
        car = scheduled_rental.reservation.car
        damage = DamageService.report_damage(
            car=car,
            description="Odprysk szyby",
            location="szyba przednia",
            severity="minor",
        )

        return_protocol = ReturnService.complete_return(
            scheduled_rental.pk,
            mileage=10_350,
            fuel_level_percent=70,
            signer_name="Jan",
            signature_image=_tiny_image("ret.png"),
        )
        doc = Document.objects.get(
            return_protocol=return_protocol,
            document_type=DocumentType.RETURN_PROTOCOL_PDF,
            version=1,
        )
        original_hash = doc.file_hash

        damage.description = "Zmieniony opis w flocie po zwrocie"
        damage.save(update_fields=["description"])

        doc.refresh_from_db()
        assert doc.file_hash == original_hash

    def test_regenerated_handover_pdf_matches_original_after_damage_edit(
        self,
        scheduled_rental,
    ) -> None:
        car = scheduled_rental.reservation.car
        DamageService.report_damage(
            car=car,
            description="Rysa",
            location="bok",
            severity="minor",
        )
        handover = HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_200,
            fuel_level_percent=90,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )
        original = Document.objects.get(
            handover_protocol=handover,
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            version=1,
        )

        snap = handover.damage_snapshots.first()
        assert snap is not None
        damage = snap.source_damage
        assert damage is not None
        damage.description = "Edycja w fleet po wygenerowaniu PDF"
        damage.save(update_fields=["description"])

        from apps.documents.services.document import DocumentService

        regenerated = DocumentService.generate_handover_pdf(handover.pk)
        assert regenerated.version == 2
        assert regenerated.file_hash == original.file_hash


@pytest.mark.django_db
class TestEmailFailureIntegration:
    def test_handover_succeeds_when_customer_has_no_email(
        self,
        scheduled_rental,
    ) -> None:
        customer = scheduled_rental.reservation.customer
        Customer.objects.filter(pk=customer.pk).update(email="", phone="600700800")
        customer.refresh_from_db()

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

        doc = Document.objects.get(
            handover_protocol=handover,
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
        )
        assert doc.file_hash
        assert doc.file_size_bytes > 0

        failed_log = doc.email_logs.filter(status=EmailStatus.FAILED).first()
        assert failed_log is not None
        assert "email" in failed_log.error_message.lower()

    @patch(
        "apps.documents.services.email.EmailMultiAlternatives.send",
        side_effect=OSError("SMTP connection refused"),
    )
    def test_handover_not_rolled_back_when_smtp_fails(
        self,
        _mock_send,
        scheduled_rental,
    ) -> None:
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

        doc = Document.objects.get(
            handover_protocol=handover,
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
        )
        log = doc.email_logs.order_by("-created_at").first()
        assert log is not None
        assert log.status == EmailStatus.FAILED
        assert "SMTP" in log.error_message

    @patch(
        "apps.documents.services.email.EmailMultiAlternatives.send",
        side_effect=OSError("SMTP connection refused"),
    )
    def test_return_not_rolled_back_when_smtp_fails(
        self,
        _mock_send,
        scheduled_rental,
    ) -> None:
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )

        return_protocol = ReturnService.complete_return(
            scheduled_rental.pk,
            mileage=10_300,
            fuel_level_percent=80,
            signer_name="Jan",
            signature_image=_tiny_image("ret.png"),
        )
        scheduled_rental.refresh_from_db()

        assert return_protocol.is_completed
        assert scheduled_rental.status == RentalStatus.RETURNED

        doc = Document.objects.get(
            return_protocol=return_protocol,
            document_type=DocumentType.RETURN_PROTOCOL_PDF,
        )
        log = doc.email_logs.order_by("-created_at").first()
        assert log is not None
        assert log.status == EmailStatus.FAILED


@pytest.mark.django_db
class TestInvoicePdfImmutabilityIntegration:
    def test_invoice_pdf_unchanged_after_price_line_edit(
        self,
        scheduled_rental,
    ) -> None:
        invoice, document = InvoiceService.create_issue_and_generate_pdf(
            scheduled_rental.pk,
        )
        original_hash = document.file_hash

        price_line = scheduled_rental.reservation.price_lines.first()
        assert price_line is not None
        price_line.description = "Zmieniony opis pozycji w rezerwacji"
        price_line.save(update_fields=["description"])

        document.refresh_from_db()
        assert document.file_hash == original_hash
        assert invoice.items.first().description != price_line.description
