"""Wspolne fixtury pytest."""

from __future__ import annotations

import pytest

from apps.documents.pdf_test_support import (
    deterministic_stub_pdf,
    weasyprint_available,
)
from apps.documents.services.pdf_renderer import PdfRenderer


@pytest.fixture(autouse=True)
def stub_pdf_renderer_without_weasyprint(monkeypatch: pytest.MonkeyPatch) -> None:
    if weasyprint_available():
        return
    monkeypatch.setattr(
        PdfRenderer,
        "html_to_pdf",
        staticmethod(deterministic_stub_pdf),
    )
