from __future__ import annotations

import hashlib
from typing import Any

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.template.loader import render_to_string

from apps.documents.constants import DEFAULT_TEMPLATE_PATHS
from apps.documents.dto.protocol import HandoverDocumentData, ReturnDocumentData
from apps.documents.models import Document, DocumentTemplate, DocumentType
from apps.documents.selectors.invoice_data import (
    build_invoice_document_data,
    get_invoice_by_id,
)
from apps.documents.selectors.protocol_data import (
    build_handover_document_data,
    build_return_document_data,
)
from apps.documents.services.document_sms import DocumentSmsService
from apps.documents.services.email import EmailService
from apps.documents.services.pdf_renderer import PdfRenderer
from apps.operations.models import HandoverProtocol, ReturnProtocol


class DocumentService:
    @staticmethod
    def _sha256_hex(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _content_hash_from_html(html: str) -> str:
        """Hash kanonicznej tresci HTML — stabilny miedzy renderami WeasyPrint."""
        return DocumentService._sha256_hex(html.encode("utf-8"))

    @staticmethod
    def _render_template(
        template_name: str,
        context: dict[str, Any],
    ) -> tuple[str, bytes]:
        html = render_to_string(template_name, context)
        pdf_bytes = PdfRenderer.html_to_pdf(html)
        return html, pdf_bytes

    @staticmethod
    def _resolve_template(document_type: str) -> tuple[str, DocumentTemplate | None]:
        template = (
            DocumentTemplate.objects.filter(
                document_type=document_type,
                is_active=True,
            )
            .order_by("-updated_at")
            .first()
        )
        if template is not None:
            return template.template_path, template
        fallback = DEFAULT_TEMPLATE_PATHS.get(document_type)
        if fallback is None:
            raise ValidationError(f"Brak szablonu dla typu dokumentu: {document_type}")
        return fallback, None

    @staticmethod
    def _next_version(
        document_type: str,
        *,
        handover_protocol_id: int | None = None,
        return_protocol_id: int | None = None,
        invoice_id: int | None = None,
    ) -> int:
        qs = Document.objects.filter(document_type=document_type)
        if handover_protocol_id is not None:
            qs = qs.filter(handover_protocol_id=handover_protocol_id)
        if return_protocol_id is not None:
            qs = qs.filter(return_protocol_id=return_protocol_id)
        if invoice_id is not None:
            qs = qs.filter(invoice_id=invoice_id)
        return qs.count() + 1

    @staticmethod
    def _store_pdf(
        *,
        pdf_bytes: bytes,
        html_content: str,
        document_type: str,
        template: DocumentTemplate | None,
        rental_id: int,
        customer_id: int,
        title: str,
        version: int,
        filename_stem: str,
        generated_by_id: int | None,
        handover_protocol_id: int | None = None,
        return_protocol_id: int | None = None,
        invoice_id: int | None = None,
        send_email: bool = True,
    ) -> Document:
        file_hash = DocumentService._content_hash_from_html(html_content)
        document = Document(
            document_type=document_type,
            template=template,
            rental_id=rental_id,
            customer_id=customer_id,
            handover_protocol_id=handover_protocol_id,
            return_protocol_id=return_protocol_id,
            invoice_id=invoice_id,
            file_hash=file_hash,
            file_size_bytes=len(pdf_bytes),
            version=version,
            title=title,
            generated_by_id=generated_by_id,
        )
        filename = f"{filename_stem}_v{version}.pdf"
        document.file.save(filename, ContentFile(pdf_bytes), save=False)
        document.save()
        if send_email:
            EmailService.enqueue_document_email(
                document.pk,
                sent_by_id=generated_by_id,
            )
            DocumentSmsService.enqueue_document_sms(
                document.pk,
                sent_by_id=generated_by_id,
            )
        return document

    @staticmethod
    def generate_handover_pdf(
        handover_id: int,
        *,
        generated_by_id: int | None = None,
    ) -> Document:
        handover = (
            HandoverProtocol.objects.select_related(
                "rental",
                "rental__reservation",
                "rental__reservation__customer",
                "rental__reservation__car",
                "signature",
            )
            .prefetch_related("damage_snapshots")
            .filter(pk=handover_id)
            .first()
        )
        if handover is None:
            raise ValidationError(f"Protokol wydania {handover_id} nie istnieje.")

        data = build_handover_document_data(handover)
        return DocumentService._generate_handover_from_data(
            data,
            customer_id=handover.rental.reservation.customer_id,
            generated_by_id=generated_by_id,
        )

    @staticmethod
    def generate_return_pdf(
        return_protocol_id: int,
        *,
        generated_by_id: int | None = None,
    ) -> Document:
        return_protocol = (
            ReturnProtocol.objects.select_related(
                "rental",
                "rental__reservation",
                "rental__reservation__customer",
                "rental__reservation__car",
                "handover",
                "signature",
            )
            .prefetch_related("damage_snapshots")
            .filter(pk=return_protocol_id)
            .first()
        )
        if return_protocol is None:
            raise ValidationError(f"Protokol zwrotu {return_protocol_id} nie istnieje.")

        data = build_return_document_data(return_protocol)
        return DocumentService._generate_return_from_data(
            data,
            customer_id=return_protocol.rental.reservation.customer_id,
            generated_by_id=generated_by_id,
        )

    @staticmethod
    @transaction.atomic
    def _generate_handover_from_data(
        data: HandoverDocumentData,
        *,
        customer_id: int,
        generated_by_id: int | None,
    ) -> Document:
        template_path, template = DocumentService._resolve_template(
            DocumentType.HANDOVER_PROTOCOL_PDF
        )
        html_content, pdf_bytes = DocumentService._render_template(
            template_path,
            data.as_template_context(),
        )
        version = DocumentService._next_version(
            DocumentType.HANDOVER_PROTOCOL_PDF,
            handover_protocol_id=data.handover_protocol_id,
        )
        return DocumentService._store_pdf(
            pdf_bytes=pdf_bytes,
            html_content=html_content,
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            template=template,
            rental_id=data.rental_id,
            customer_id=customer_id,
            title=f"Protokol wydania — wynajem #{data.rental_id}",
            version=version,
            filename_stem="protokol_wydania",
            generated_by_id=generated_by_id,
            handover_protocol_id=data.handover_protocol_id,
        )

    @staticmethod
    @transaction.atomic
    def _generate_return_from_data(
        data: ReturnDocumentData,
        *,
        customer_id: int,
        generated_by_id: int | None,
    ) -> Document:
        template_path, template = DocumentService._resolve_template(
            DocumentType.RETURN_PROTOCOL_PDF
        )
        html_content, pdf_bytes = DocumentService._render_template(
            template_path,
            data.as_template_context(),
        )
        version = DocumentService._next_version(
            DocumentType.RETURN_PROTOCOL_PDF,
            return_protocol_id=data.return_protocol_id,
        )
        return DocumentService._store_pdf(
            pdf_bytes=pdf_bytes,
            html_content=html_content,
            document_type=DocumentType.RETURN_PROTOCOL_PDF,
            template=template,
            rental_id=data.rental_id,
            customer_id=customer_id,
            title=f"Protokol zwrotu — wynajem #{data.rental_id}",
            version=version,
            filename_stem="protokol_zwrotu",
            generated_by_id=generated_by_id,
            return_protocol_id=data.return_protocol_id,
        )

    @staticmethod
    def regenerate_handover_pdf(
        handover_id: int,
        *,
        generated_by_id: int | None = None,
    ) -> Document:
        """Generate a new versioned Document for an existing handover protocol."""
        return DocumentService.generate_handover_pdf(
            handover_id,
            generated_by_id=generated_by_id,
        )

    @staticmethod
    def regenerate_return_pdf(
        return_protocol_id: int,
        *,
        generated_by_id: int | None = None,
    ) -> Document:
        return DocumentService.generate_return_pdf(
            return_protocol_id,
            generated_by_id=generated_by_id,
        )

    @staticmethod
    @transaction.atomic
    def generate_invoice_pdf(
        invoice_id: int,
        *,
        generated_by_id: int | None = None,
    ) -> Document:
        invoice = get_invoice_by_id(invoice_id)
        if invoice is None:
            raise ValidationError(f"Faktura {invoice_id} nie istnieje.")

        data = build_invoice_document_data(invoice)
        template_path, template = DocumentService._resolve_template(
            DocumentType.INVOICE_PDF
        )
        html_content, pdf_bytes = DocumentService._render_template(
            template_path,
            data.as_template_context(),
        )
        version = DocumentService._next_version(
            DocumentType.INVOICE_PDF,
            invoice_id=invoice.pk,
        )
        return DocumentService._store_pdf(
            pdf_bytes=pdf_bytes,
            html_content=html_content,
            document_type=DocumentType.INVOICE_PDF,
            template=template,
            rental_id=invoice.rental_id,
            customer_id=invoice.customer_id,
            title=f"Faktura {invoice.invoice_number}",
            version=version,
            filename_stem=f"faktura_{invoice.invoice_number.replace('/', '_')}",
            generated_by_id=generated_by_id,
            invoice_id=invoice.pk,
            send_email=False,
        )
