from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, PriceLine, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.models import (
    Document,
    DocumentType,
    InvoiceStatus,
)
from apps.documents.services.document import DocumentService
from apps.documents.services.invoice import InvoiceService
from apps.documents.services.pdf_renderer import PdfRenderer
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV", slug="suv-invoice", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Invoice tests",
        slug="invoice-tests",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("100"))
    return pl


@pytest.fixture
def rental_with_price_lines(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Anna",
        last_name="Nowak",
        email="anna@invoice.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1INV01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
    )
    start = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)
    end = datetime(2026, 8, 14, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)


@pytest.mark.django_db
class TestInvoiceService:
    def test_create_from_rental_copies_price_lines(
        self,
        rental_with_price_lines,
    ) -> None:
        invoice = InvoiceService.create_from_rental(
            rental_with_price_lines.pk,
            issue_date=date(2026, 8, 15),
        )

        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.invoice_number == "FV/2026/0001"
        assert invoice.customer_id == rental_with_price_lines.reservation.customer_id
        assert (
            invoice.items.count()
            == rental_with_price_lines.reservation.price_lines.count()
        )

        price_line = rental_with_price_lines.reservation.price_lines.first()
        item = invoice.items.first()
        assert item is not None
        assert price_line is not None
        assert item.description == price_line.description
        assert item.quantity == price_line.quantity
        assert item.unit_price == price_line.unit_price
        assert item.line_total == price_line.total_amount
        assert item.price_line_id == price_line.pk
        assert invoice.total_amount == sum(
            line.total_amount
            for line in rental_with_price_lines.reservation.price_lines.all()
        )

    def test_create_rejects_rental_without_price_lines(
        self,
        rental_with_price_lines,
    ) -> None:
        PriceLine.objects.filter(
            reservation=rental_with_price_lines.reservation
        ).delete()
        with pytest.raises(ValidationError, match="snapshotu ceny"):
            InvoiceService.create_from_rental(rental_with_price_lines.pk)

    def test_create_rejects_duplicate_active_invoice(
        self,
        rental_with_price_lines,
    ) -> None:
        InvoiceService.create_from_rental(rental_with_price_lines.pk)
        with pytest.raises(ValidationError, match="aktywna faktura"):
            InvoiceService.create_from_rental(rental_with_price_lines.pk)

    def test_issue_changes_status(self, rental_with_price_lines) -> None:
        invoice = InvoiceService.create_from_rental(rental_with_price_lines.pk)
        issued = InvoiceService.issue(invoice.pk)
        assert issued.status == InvoiceStatus.ISSUED

    def test_issue_rejects_non_draft(self, rental_with_price_lines) -> None:
        invoice = InvoiceService.create_from_rental(rental_with_price_lines.pk)
        InvoiceService.issue(invoice.pk)
        with pytest.raises(ValidationError, match="szkic"):
            InvoiceService.issue(invoice.pk)

    def test_generate_pdf_creates_document(
        self,
        rental_with_price_lines,
    ) -> None:
        invoice = InvoiceService.create_from_rental(rental_with_price_lines.pk)
        InvoiceService.issue(invoice.pk)

        document = InvoiceService.generate_pdf(invoice.pk)
        assert document.document_type == DocumentType.INVOICE_PDF
        assert document.invoice_id == invoice.pk
        assert document.rental_id == rental_with_price_lines.pk
        assert document.version == 1
        assert len(document.file_hash) == 64

        path = settings.DOCUMENTS_PRIVATE_ROOT / document.file.name
        assert path.is_file()
        assert PdfRenderer.is_pdf(path.read_bytes())

    def test_pdf_unchanged_after_price_line_edit(
        self,
        rental_with_price_lines,
    ) -> None:
        invoice = InvoiceService.create_from_rental(rental_with_price_lines.pk)
        InvoiceService.issue(invoice.pk)
        first = InvoiceService.generate_pdf(invoice.pk)

        price_line = rental_with_price_lines.reservation.price_lines.first()
        assert price_line is not None
        price_line.description = "Zmieniony opis w rezerwacji"
        price_line.save(update_fields=["description"])

        second = InvoiceService.generate_pdf(invoice.pk)
        assert second.file_hash == first.file_hash
        assert second.version == 2

    def test_create_issue_and_generate_pdf(
        self,
        rental_with_price_lines,
    ) -> None:
        invoice, document = InvoiceService.create_issue_and_generate_pdf(
            rental_with_price_lines.pk,
            issue_date=date(2026, 8, 20),
        )
        assert invoice.status == InvoiceStatus.ISSUED
        assert document.invoice_id == invoice.pk
        assert Document.objects.filter(invoice=invoice).count() == 1

    def test_invoice_number_sequence(self, rental_with_price_lines) -> None:
        first = InvoiceService.create_from_rental(
            rental_with_price_lines.pk,
            issue_date=date(2026, 1, 1),
        )
        first.status = InvoiceStatus.CANCELLED
        first.save(update_fields=["status"])

        customer = Customer.objects.create(
            first_name="Jan",
            last_name="Kowalski",
            email="jan@invoice.test",
        )
        car = Car.objects.create(
            category=rental_with_price_lines.reservation.car.category,
            registration_number="KR1INV02",
            make="Honda",
            model="Civic",
            year=2021,
            status=CarStatus.ACTIVE,
            mileage=20_000,
        )
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 9, 5, 10, 0, tzinfo=UTC),
            status=ReservationStatus.CONFIRMED,
        )
        rental2 = RentalService.convert_from_reservation(reservation)

        second = InvoiceService.create_from_rental(
            rental2.pk,
            issue_date=date(2026, 1, 15),
        )
        assert first.invoice_number == "FV/2026/0001"
        assert second.invoice_number == "FV/2026/0002"

    def test_document_service_generate_invoice_pdf(
        self,
        rental_with_price_lines,
    ) -> None:
        invoice = InvoiceService.create_from_rental(rental_with_price_lines.pk)
        InvoiceService.issue(invoice.pk)
        doc = DocumentService.generate_invoice_pdf(invoice.pk)
        assert doc.document_type == DocumentType.INVOICE_PDF
