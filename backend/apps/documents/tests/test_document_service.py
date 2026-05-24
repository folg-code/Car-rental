from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.models import Document, DocumentType
from apps.documents.services.document import DocumentService
from apps.documents.services.pdf_renderer import PdfRenderer
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.fleet.services.damage import DamageService
from apps.operations.models import HandoverProtocol
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
        name="SUV", slug="suv-doc-svc", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Doc Svc",
        slug="doc-svc",
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
        email="jan@doc-svc.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1SVC01",
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


@pytest.fixture
def completed_handover(scheduled_rental) -> HandoverProtocol:
    car = scheduled_rental.reservation.car
    DamageService.report_damage(
        car=car,
        description="Rysa na drzwiach",
        location="lewe przednie",
        severity="minor",
    )
    return HandoverService.complete_handover(
        scheduled_rental.pk,
        mileage=10_200,
        fuel_level_percent=90,
        signer_name="Jan Kowalski",
        signature_image=_tiny_image(),
        notes="Stan OK.",
    )


@pytest.mark.django_db
class TestDocumentService:
    def test_generate_handover_pdf_creates_document(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        assert (
            Document.objects.filter(
                handover_protocol=completed_handover,
                document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            ).count()
            == 1
        )

        doc = DocumentService.generate_handover_pdf(completed_handover.pk)
        assert doc.pk is not None
        assert doc.document_type == DocumentType.HANDOVER_PROTOCOL_PDF
        assert doc.handover_protocol_id == completed_handover.pk
        assert doc.rental_id == completed_handover.rental_id
        assert doc.version == 2
        assert len(doc.file_hash) == 64
        assert doc.file_size_bytes > 0
        assert doc.file.name.endswith(".pdf")
        path = settings.DOCUMENTS_PRIVATE_ROOT / doc.file.name
        assert path.is_file()
        assert PdfRenderer.is_pdf(path.read_bytes())

    def test_regenerate_increments_version(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        first = DocumentService.regenerate_handover_pdf(completed_handover.pk)
        second = DocumentService.regenerate_handover_pdf(completed_handover.pk)
        assert first.pk != second.pk
        assert first.version == 2
        assert second.version == 3
        assert (
            Document.objects.filter(
                handover_protocol=completed_handover,
                document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            ).count()
            == 3
        )

    def test_pdf_hash_stable_after_fleet_damage_edit(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        first = DocumentService.regenerate_handover_pdf(completed_handover.pk)
        snap = completed_handover.damage_snapshots.first()
        assert snap is not None
        damage = snap.source_damage
        assert damage is not None
        damage.description = "Zmieniony opis w flocie"
        damage.save(update_fields=["description"])

        second = DocumentService.regenerate_handover_pdf(completed_handover.pk)
        assert second.file_hash == first.file_hash

    def test_generate_return_pdf(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        return_protocol = ReturnService.complete_return(
            completed_handover.rental_id,
            mileage=10_450,
            fuel_level_percent=70,
            signer_name="Jan Kowalski",
            signature_image=_tiny_image("ret.png"),
        )
        assert (
            Document.objects.filter(
                return_protocol=return_protocol,
                document_type=DocumentType.RETURN_PROTOCOL_PDF,
            ).count()
            == 1
        )

        doc = DocumentService.generate_return_pdf(return_protocol.pk)
        assert doc.document_type == DocumentType.RETURN_PROTOCOL_PDF
        assert doc.return_protocol_id == return_protocol.pk
        assert doc.version == 2

    def test_rejects_incomplete_handover(self, scheduled_rental) -> None:
        handover = HandoverProtocol.objects.create(
            rental=scheduled_rental,
            mileage=10_100,
            fuel_level_percent=100,
        )
        with pytest.raises(ValidationError, match="zakonczonego"):
            DocumentService.generate_handover_pdf(handover.pk)
