"""Default Django template paths for PDF generation."""

HANDOVER_PROTOCOL_PDF_TEMPLATE = "documents/pdf/handover_protocol.html"
RETURN_PROTOCOL_PDF_TEMPLATE = "documents/pdf/return_protocol.html"
INVOICE_PDF_TEMPLATE = "documents/pdf/invoice.html"

DEFAULT_TEMPLATE_PATHS: dict[str, str] = {
    "handover_protocol_pdf": HANDOVER_PROTOCOL_PDF_TEMPLATE,
    "return_protocol_pdf": RETURN_PROTOCOL_PDF_TEMPLATE,
    "invoice_pdf": INVOICE_PDF_TEMPLATE,
}

HANDOVER_EMAIL_SUBJECT = "documents/email/handover_subject.txt"
HANDOVER_EMAIL_BODY_TEXT = "documents/email/handover_body.txt"
HANDOVER_EMAIL_BODY_HTML = "documents/email/handover_body.html"

RETURN_EMAIL_SUBJECT = "documents/email/return_subject.txt"
RETURN_EMAIL_BODY_TEXT = "documents/email/return_body.txt"
RETURN_EMAIL_BODY_HTML = "documents/email/return_body.html"

EMAIL_TEMPLATES_BY_DOCUMENT_TYPE: dict[str, dict[str, str]] = {
    "handover_protocol_pdf": {
        "subject": HANDOVER_EMAIL_SUBJECT,
        "text": HANDOVER_EMAIL_BODY_TEXT,
        "html": HANDOVER_EMAIL_BODY_HTML,
    },
    "return_protocol_pdf": {
        "subject": RETURN_EMAIL_SUBJECT,
        "text": RETURN_EMAIL_BODY_TEXT,
        "html": RETURN_EMAIL_BODY_HTML,
    },
}

SMS_TEMPLATES_BY_DOCUMENT_TYPE: dict[str, str] = {
    "handover_protocol_pdf": "documents/sms/handover.txt",
    "return_protocol_pdf": "documents/sms/return.txt",
}
