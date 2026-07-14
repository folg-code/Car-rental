from datetime import UTC, datetime

import pytest

from apps.documents.constants import (
    HANDOVER_PROTOCOL_PDF_TEMPLATE,
    RETURN_PROTOCOL_PDF_TEMPLATE,
)
from apps.documents.services.pdf_renderer import PdfRenderer


@pytest.fixture
def handover_pdf_context() -> dict:
    return {
        "rental_id": 42,
        "customer_name": "Anna Nowak",
        "car_label": "Toyota Yaris",
        "registration_number": "KR1TEST",
        "mileage": 10_200,
        "fuel_level_percent": 100,
        "notes": "Brak uwag.",
        "completed_at": datetime(2026, 5, 20, 10, 30, tzinfo=UTC),
        "damages": [
            {
                "description": "Rysa na zderzaku",
                "location": "Przod",
                "severity": "minor",
                "is_new": False,
            }
        ],
        "signature_name": "Anna Nowak",
    }


@pytest.fixture
def return_pdf_context(handover_pdf_context: dict) -> dict:
    return {
        **handover_pdf_context,
        "handover_mileage": 10_200,
        "handover_fuel_level_percent": 100,
        "mileage": 10_450,
        "fuel_level_percent": 75,
        "mileage_driven": 250,
        "surcharge_notes": "Uzupelnienie paliwa — do rozliczenia.",
        "damages": [
            {
                "description": "Rysa na zderzaku",
                "location": "Przod",
                "severity": "minor",
                "is_new": False,
            },
            {
                "description": "Odprysk szyby",
                "location": "Szyba przednia",
                "severity": "minor",
                "is_new": True,
            },
        ],
    }


@pytest.mark.django_db
class TestPdfRenderer:
    def test_html_to_pdf_returns_pdf_magic_bytes(self) -> None:
        pdf_bytes = PdfRenderer.html_to_pdf(
            "<html><body><p>Test protokolu</p></body></html>"
        )
        assert PdfRenderer.is_pdf(pdf_bytes)
        assert len(pdf_bytes) > 100

    def test_render_handover_protocol_template(
        self,
        handover_pdf_context: dict,
    ) -> None:
        pdf_bytes = PdfRenderer.render_template(
            HANDOVER_PROTOCOL_PDF_TEMPLATE,
            handover_pdf_context,
        )
        assert PdfRenderer.is_pdf(pdf_bytes)
        assert len(pdf_bytes) > 500

    def test_render_return_protocol_template(
        self,
        return_pdf_context: dict,
    ) -> None:
        pdf_bytes = PdfRenderer.render_template(
            RETURN_PROTOCOL_PDF_TEMPLATE,
            return_pdf_context,
        )
        assert PdfRenderer.is_pdf(pdf_bytes)

    def test_stabilize_pdf_bytes_normalizes_volatile_metadata(self) -> None:
        raw = (
            b"%PDF-1.7\n"
            b"1 0 obj<</CreationDate (D:20250601120000+00'00')"
            b"/ModDate (D:20250601120000+00'00')"
            b"/ID [<aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa> "
            b"<bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb>]>>"
            b"endobj\n%%EOF\n"
        )
        stabilized = PdfRenderer._stabilize_pdf_bytes(raw)
        assert b"/CreationDate (D:20200101000000+00'00')" in stabilized
        assert b"/ModDate (D:20200101000000+00'00')" in stabilized
        assert (
            b"/ID [<00000000000000000000000000000000> "
            b"<00000000000000000000000000000000>]"
        ) in stabilized
        assert b"20250601120000" not in stabilized

    def test_stabilize_pdf_bytes_is_idempotent(self) -> None:
        raw = (
            b"%PDF-1.7\n"
            b"1 0 obj<</CreationDate (D:20250601120000)/ModDate (D:20250601120000)"
            b"/ID [<abcd> <efgh>]>>endobj\n%%EOF\n"
        )
        once = PdfRenderer._stabilize_pdf_bytes(raw)
        twice = PdfRenderer._stabilize_pdf_bytes(once)
        assert once == twice
