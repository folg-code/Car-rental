"""Pomocniki testowe PDF — fallback gdy brak natywnych bibliotek WeasyPrint."""

from __future__ import annotations

import hashlib

from apps.documents.services.pdf_renderer import PdfRenderer

_weasyprint_available: bool | None = None


def weasyprint_available() -> bool:
    """Czy WeasyPrint moze zaladowac libgobject/pango (Docker/CI vs Windows dev)."""
    global _weasyprint_available
    if _weasyprint_available is None:
        try:
            from weasyprint import HTML  # noqa: F401
        except OSError:
            _weasyprint_available = False
        else:
            _weasyprint_available = True
    return _weasyprint_available


def deterministic_stub_pdf(html: str, base_url: str | None = None) -> bytes:
    """Minimalny, deterministyczny PDF z hasha HTML — do testow bez WeasyPrint."""
    digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
    padding = "0" * 480
    body = (
        f"%PDF-1.4\n"
        f"1 0 obj<</Length {len(digest) + len(padding)}>>stream\n"
        f"{digest}{padding}\n"
        f"endstream\nendobj\n%%EOF\n"
    ).encode("ascii")
    return PdfRenderer._stabilize_pdf_bytes(body)
