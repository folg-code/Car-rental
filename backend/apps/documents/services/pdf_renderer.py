from __future__ import annotations

import re
from io import BytesIO
from typing import Any

from django.template.loader import render_to_string

# Stabilne metadane — identyczna tresc HTML daje ten sam hash PDF miedzy renderami.
_PDF_CREATION_DATE = b"/CreationDate (D:20200101000000+00'00')"
_PDF_MOD_DATE = b"/ModDate (D:20200101000000+00'00')"
_PDF_ID = b"/ID [<00000000000000000000000000000000> <00000000000000000000000000000000>]"


class PdfRenderer:
    """Render Django HTML templates to PDF bytes via WeasyPrint."""

    @staticmethod
    def render_template(template_name: str, context: dict[str, Any]) -> bytes:
        html = render_to_string(template_name, context)
        return PdfRenderer.html_to_pdf(html)

    @staticmethod
    def html_to_pdf(html: str, base_url: str | None = None) -> bytes:
        from weasyprint import HTML

        buffer = BytesIO()
        HTML(string=html, base_url=base_url).write_pdf(buffer)
        return PdfRenderer._stabilize_pdf_bytes(buffer.getvalue())

    @staticmethod
    def _stabilize_pdf_bytes(pdf_bytes: bytes) -> bytes:
        """Usuwa znaczniki czasu z metadanych PDF dla powtarzalnych hashy tresci."""
        pdf_bytes = re.sub(
            rb"/CreationDate\s*\([^)]*\)",
            _PDF_CREATION_DATE,
            pdf_bytes,
        )
        pdf_bytes = re.sub(
            rb"/ModDate\s*\([^)]*\)",
            _PDF_MOD_DATE,
            pdf_bytes,
        )
        pdf_bytes = re.sub(
            rb"/ID\s*\[<[^>]*>\s*<[^>]*>\]",
            _PDF_ID,
            pdf_bytes,
        )
        return pdf_bytes

    @staticmethod
    def is_pdf(content: bytes) -> bool:
        return content.startswith(b"%PDF")
