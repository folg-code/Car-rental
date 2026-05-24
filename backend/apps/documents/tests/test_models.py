from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import (
    Document,
    DocumentTemplate,
    DocumentType,
    EmailLog,
    EmailStatus,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
)


@pytest.fixture
def handover_template(db) -> DocumentTemplate:
    return DocumentTemplate.objects.create(
        name="Protokol wydania v1",
        slug="handover-v1",
        document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
        template_path="documents/pdf/handover_protocol.html",
    )


@pytest.fixture
def sample_pdf() -> SimpleUploadedFile:
    return SimpleUploadedFile(
        "protokol.pdf",
        b"%PDF-1.4 test content",
        content_type="application/pdf",
    )


@pytest.mark.django_db
class TestDocumentTemplate:
    def test_create(self, handover_template: DocumentTemplate) -> None:
        assert handover_template.is_active is True
        assert handover_template.slug == "handover-v1"


@pytest.mark.django_db
class TestDocument:
    def test_handover_pdf_requires_protocol(
        self, sample_pdf: SimpleUploadedFile
    ) -> None:
        doc = Document(
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            file=sample_pdf,
        )
        with pytest.raises(ValidationError) as exc:
            doc.save()
        assert "handover_protocol" in exc.value.message_dict

    def test_file_immutable_after_create(
        self,
        scheduled_rental,
        sample_pdf: SimpleUploadedFile,
    ) -> None:
        from apps.operations.models import HandoverProtocol

        handover = HandoverProtocol.objects.create(
            rental=scheduled_rental,
            mileage=10_000,
            fuel_level_percent=100,
            completed_at="2026-05-20T10:00:00Z",
        )
        doc = Document.objects.create(
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            rental=scheduled_rental,
            handover_protocol=handover,
            file=sample_pdf,
            file_hash="abc123",
            file_size_bytes=100,
            title="Protokol wydania",
        )
        doc.file = SimpleUploadedFile(
            "other.pdf",
            b"%PDF other",
            content_type="application/pdf",
        )
        with pytest.raises(ValidationError, match="nie moze byc zmieniony"):
            doc.save()


@pytest.mark.django_db
class TestEmailLog:
    def test_create_pending(
        self,
        scheduled_rental,
        sample_pdf: SimpleUploadedFile,
    ) -> None:
        from apps.operations.models import HandoverProtocol

        handover = HandoverProtocol.objects.create(
            rental=scheduled_rental,
            mileage=10_000,
            fuel_level_percent=100,
            completed_at="2026-05-20T10:00:00Z",
        )
        doc = Document.objects.create(
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            rental=scheduled_rental,
            handover_protocol=handover,
            file=sample_pdf,
            file_size_bytes=100,
        )
        log = EmailLog.objects.create(
            document=doc,
            recipient_email="klient@example.com",
            subject="Protokol wydania",
            status=EmailStatus.PENDING,
        )
        assert log.status == EmailStatus.PENDING


@pytest.mark.django_db
class TestInvoice:
    def test_invoice_item_line_total_validation(
        self,
        scheduled_rental,
    ) -> None:
        customer = scheduled_rental.reservation.customer
        invoice = Invoice.objects.create(
            rental=scheduled_rental,
            customer=customer,
            invoice_number="FV/2026/001",
            issue_date="2026-05-20",
            status=InvoiceStatus.ISSUED,
            total_amount=Decimal("500.00"),
        )
        item = InvoiceItem(
            invoice=invoice,
            description="Wynajem 5 dni",
            quantity=Decimal("5"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("499.00"),
        )
        with pytest.raises(ValidationError) as exc:
            item.save()
        assert "line_total" in exc.value.message_dict

    def test_invoice_item_valid_line(
        self,
        scheduled_rental,
    ) -> None:
        customer = scheduled_rental.reservation.customer
        invoice = Invoice.objects.create(
            rental=scheduled_rental,
            customer=customer,
            invoice_number="FV/2026/002",
            issue_date="2026-05-20",
            total_amount=Decimal("300.00"),
        )
        item = InvoiceItem.objects.create(
            invoice=invoice,
            description="Wynajem 3 dni",
            quantity=Decimal("3"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("300.00"),
        )
        assert item.line_total == Decimal("300.00")
