from __future__ import annotations

from io import BytesIO
from typing import Any

from django.template.loader import render_to_string


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
        return buffer.getvalue()

    @staticmethod
    def is_pdf(content: bytes) -> bool:
        return content.startswith(b"%PDF")
