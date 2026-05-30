from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import PriceLine
from apps.bookings.selectors.rental import get_rental_by_id
from apps.documents.models import Document, Invoice, InvoiceItem, InvoiceStatus
from apps.documents.selectors.invoice_data import rental_has_active_invoice
from apps.documents.services.document import DocumentService


class InvoiceService:
    @staticmethod
    def _next_invoice_number(issue_date: date) -> str:
        prefix = f"FV/{issue_date.year}/"
        last_number = (
            Invoice.objects.filter(invoice_number__startswith=prefix)
            .order_by("-invoice_number")
            .values_list("invoice_number", flat=True)
            .first()
        )
        if last_number:
            sequence = int(last_number.rsplit("/", maxsplit=1)[-1]) + 1
        else:
            sequence = 1
        return f"{prefix}{sequence:04d}"

    @staticmethod
    def _copy_price_lines_to_items(
        invoice: Invoice,
        price_lines: list[PriceLine],
    ) -> list[InvoiceItem]:
        items: list[InvoiceItem] = []
        for price_line in price_lines:
            item = InvoiceItem.objects.create(
                invoice=invoice,
                description=price_line.description,
                quantity=price_line.quantity,
                unit_price=price_line.unit_price,
                line_total=price_line.total_amount,
                price_line=price_line,
                sort_order=price_line.sort_order,
            )
            items.append(item)
        return items

    @staticmethod
    @transaction.atomic
    def create_from_rental(
        rental_id: int,
        *,
        issue_date: date | None = None,
        due_date: date | None = None,
        notes: str = "",
    ) -> Invoice:
        rental = get_rental_by_id(rental_id)
        if rental is None:
            raise ValidationError(f"Wynajem {rental_id} nie istnieje.")

        price_lines = list(rental.reservation.price_lines.order_by("sort_order", "pk"))
        if not price_lines:
            raise ValidationError(
                "Brak snapshotu ceny (PriceLine) — nie mozna wystawic faktury."
            )

        if rental_has_active_invoice(rental_id):
            raise ValidationError("Dla tego wynajmu istnieje juz aktywna faktura.")

        when = issue_date or timezone.localdate()
        invoice = Invoice.objects.create(
            rental=rental,
            customer=rental.reservation.customer,
            invoice_number=InvoiceService._next_invoice_number(when),
            issue_date=when,
            due_date=due_date or (when + timedelta(days=14)),
            status=InvoiceStatus.DRAFT,
            currency="PLN",
            notes=notes,
        )

        items = InvoiceService._copy_price_lines_to_items(invoice, price_lines)
        total = sum((item.line_total for item in items), Decimal("0")).quantize(
            Decimal("0.01")
        )
        invoice.total_amount = total
        invoice.save(update_fields=["total_amount", "updated_at"])
        return invoice

    @staticmethod
    @transaction.atomic
    def issue(invoice_id: int) -> Invoice:
        invoice = Invoice.objects.select_for_update().filter(pk=invoice_id).first()
        if invoice is None:
            raise ValidationError(f"Faktura {invoice_id} nie istnieje.")
        if invoice.status != InvoiceStatus.DRAFT:
            raise ValidationError("Mozna wystawic tylko fakture w statusie szkic.")
        if not invoice.items.exists():
            raise ValidationError("Faktura nie ma pozycji.")

        invoice.status = InvoiceStatus.ISSUED
        invoice.save(update_fields=["status", "updated_at"])
        return invoice

    @staticmethod
    def generate_pdf(
        invoice_id: int,
        *,
        generated_by_id: int | None = None,
    ) -> Document:
        invoice = (
            Invoice.objects.select_related("customer", "rental")
            .prefetch_related("items")
            .filter(pk=invoice_id)
            .first()
        )
        if invoice is None:
            raise ValidationError(f"Faktura {invoice_id} nie istnieje.")
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ValidationError("Anulowanej faktury nie mozna drukowac.")
        return DocumentService.generate_invoice_pdf(
            invoice_id,
            generated_by_id=generated_by_id,
        )

    @staticmethod
    @transaction.atomic
    def create_issue_and_generate_pdf(
        rental_id: int,
        *,
        issue_date: date | None = None,
        due_date: date | None = None,
        notes: str = "",
        generated_by_id: int | None = None,
    ) -> tuple[Invoice, Document]:
        invoice = InvoiceService.create_from_rental(
            rental_id,
            issue_date=issue_date,
            due_date=due_date,
            notes=notes,
        )
        InvoiceService.issue(invoice.pk)
        document = InvoiceService.generate_pdf(
            invoice.pk,
            generated_by_id=generated_by_id,
        )
        invoice.refresh_from_db()
        return invoice, document
