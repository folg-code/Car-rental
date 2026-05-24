"""Default Django template paths for PDF generation."""

HANDOVER_PROTOCOL_PDF_TEMPLATE = "documents/pdf/handover_protocol.html"
RETURN_PROTOCOL_PDF_TEMPLATE = "documents/pdf/return_protocol.html"
INVOICE_PDF_TEMPLATE = "documents/pdf/invoice.html"

DEFAULT_TEMPLATE_PATHS: dict[str, str] = {
    "handover_protocol_pdf": HANDOVER_PROTOCOL_PDF_TEMPLATE,
    "return_protocol_pdf": RETURN_PROTOCOL_PDF_TEMPLATE,
    "invoice_pdf": INVOICE_PDF_TEMPLATE,
}
