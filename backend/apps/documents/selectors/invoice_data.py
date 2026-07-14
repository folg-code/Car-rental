from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Count, QuerySet, Sum

from apps.documents.dto.invoice import InvoiceDocumentData, InvoiceItemData
from apps.documents.models import Invoice, InvoiceStatus


def get_invoice_by_id(invoice_id: int) -> Invoice | None:
    return (
        Invoice.objects.select_related("rental", "customer")
        .prefetch_related("items")
        .filter(pk=invoice_id)
        .first()
    )


def list_invoices_for_rental(rental_id: int) -> QuerySet[Invoice]:
    return (
        Invoice.objects.filter(rental_id=rental_id)
        .select_related("customer")
        .prefetch_related("items")
        .order_by("-issue_date", "-pk")
    )


def build_invoice_document_data(invoice: Invoice) -> InvoiceDocumentData:
    items = tuple(
        InvoiceItemData(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
        )
        for item in invoice.items.order_by("sort_order", "pk")
    )
    return InvoiceDocumentData(
        invoice_id=invoice.pk,
        invoice_number=invoice.invoice_number,
        rental_id=invoice.rental_id,
        customer_name=invoice.customer.full_name,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        currency=invoice.currency,
        total_amount=invoice.total_amount,
        notes=invoice.notes,
        items=items,
    )


def rental_has_active_invoice(rental_id: int) -> bool:
    return (
        Invoice.objects.filter(rental_id=rental_id)
        .exclude(status=InvoiceStatus.CANCELLED)
        .exists()
    )


def get_invoice_totals_in_period(
    start_date: date,
    end_date: date,
) -> tuple[Decimal, int]:
    """Suma faktur (bez anulowanych) wg daty wystawienia w przedziale dat."""
    agg = (
        Invoice.objects.filter(
            issue_date__gte=start_date,
            issue_date__lte=end_date,
        )
        .exclude(status=InvoiceStatus.CANCELLED)
        .aggregate(total=Sum("total_amount"), count=Count("pk"))
    )
    total = (agg["total"] or Decimal("0")).quantize(Decimal("0.01"))
    return total, int(agg["count"] or 0)


def list_invoices_in_period(
    start_date: date,
    end_date: date,
    *,
    limit: int | None = None,
) -> QuerySet[Invoice]:
    qs = (
        Invoice.objects.filter(
            issue_date__gte=start_date,
            issue_date__lte=end_date,
        )
        .exclude(status=InvoiceStatus.CANCELLED)
        .select_related("customer", "rental")
        .order_by("-issue_date", "-pk")
    )
    if limit is not None:
        qs = qs[:limit]
    return qs
