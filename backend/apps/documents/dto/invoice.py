from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class InvoiceItemData:
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal

    def as_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "line_total": self.line_total,
        }


@dataclass(frozen=True, slots=True)
class InvoiceDocumentData:
    """Immutable payload for invoice PDF — built from Invoice + InvoiceItem only."""

    invoice_id: int
    invoice_number: str
    rental_id: int
    customer_name: str
    issue_date: date
    due_date: date | None
    currency: str
    total_amount: Decimal
    notes: str
    items: tuple[InvoiceItemData, ...]

    def as_template_context(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "rental_id": self.rental_id,
            "customer_name": self.customer_name,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "currency": self.currency,
            "total_amount": self.total_amount,
            "notes": self.notes,
            "items": [item.as_dict() for item in self.items],
        }
