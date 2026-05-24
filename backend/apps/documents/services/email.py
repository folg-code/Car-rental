from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from apps.documents.constants import EMAIL_TEMPLATES_BY_DOCUMENT_TYPE
from apps.documents.models import Document, EmailLog, EmailStatus

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def _get_document(document_id: int) -> Document:
        document = (
            Document.objects.select_related(
                "customer",
                "rental",
                "rental__reservation",
                "rental__reservation__car",
                "handover_protocol",
                "return_protocol",
            )
            .filter(pk=document_id)
            .first()
        )
        if document is None:
            raise ValidationError(f"Dokument {document_id} nie istnieje.")
        return document

    @staticmethod
    def _build_context(document: Document) -> dict:
        car = document.rental.reservation.car
        context = {
            "customer_name": document.customer.full_name,
            "rental_id": document.rental_id,
            "document_title": document.title,
            "car_label": f"{car.make} {car.model}",
            "registration_number": car.registration_number,
        }
        if document.handover_protocol_id:
            handover = document.handover_protocol
            context["mileage"] = handover.mileage
            context["fuel_level_percent"] = handover.fuel_level_percent
            context["completed_at"] = handover.completed_at
        if document.return_protocol_id:
            ret = document.return_protocol
            context["mileage"] = ret.mileage
            context["fuel_level_percent"] = ret.fuel_level_percent
            context["completed_at"] = ret.completed_at
            context["surcharge_notes"] = ret.surcharge_notes
        return context

    @staticmethod
    def _resolve_email_templates(document_type: str) -> dict[str, str]:
        templates = EMAIL_TEMPLATES_BY_DOCUMENT_TYPE.get(document_type)
        if templates is None:
            raise ValidationError(
                f"Brak szablonu email dla typu dokumentu: {document_type}"
            )
        return templates

    @staticmethod
    def _attachment_filename(document: Document) -> str:
        return Path(document.file.name).name

    @staticmethod
    def send_document_email(
        document_id: int,
        *,
        sent_by_id: int | None = None,
        force_resend: bool = False,
    ) -> EmailLog | None:
        """
        Wyslij PDF dokumentu do klienta.

        Blad wysylki nie propaguje wyjatku — status w EmailLog (retry przez serwis).
        """
        document = EmailService._get_document(document_id)
        recipient = (document.customer.email or "").strip()
        if not recipient:
            return EmailLog.objects.create(
                document=document,
                recipient_email="",
                subject=document.title[:255],
                status=EmailStatus.FAILED,
                error_message="Klient nie ma adresu email.",
                sent_by_id=sent_by_id,
            )

        if not force_resend:
            existing = (
                document.email_logs.filter(
                    recipient_email=recipient,
                    status=EmailStatus.SENT,
                )
                .order_by("-sent_at")
                .first()
            )
            if existing is not None:
                return existing

        templates = EmailService._resolve_email_templates(document.document_type)
        context = EmailService._build_context(document)
        subject = render_to_string(templates["subject"], context).strip()
        text_body = render_to_string(templates["text"], context)
        html_body = render_to_string(templates["html"], context)

        log = EmailLog.objects.create(
            document=document,
            recipient_email=recipient,
            subject=subject[:255],
            status=EmailStatus.PENDING,
            sent_by_id=sent_by_id,
        )

        try:
            with document.file.open("rb") as pdf_file:
                pdf_bytes = pdf_file.read()

            message = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
            )
            message.attach_alternative(html_body, "text/html")
            message.attach(
                EmailService._attachment_filename(document),
                pdf_bytes,
                document.content_type,
            )
            message.send(fail_silently=False)

            log.status = EmailStatus.SENT
            log.sent_at = timezone.now()
            log.error_message = ""
            log.save(update_fields=["status", "sent_at", "error_message"])
            return log
        except Exception as exc:
            logger.exception("Email send failed for document %s", document_id)
            log.status = EmailStatus.FAILED
            log.error_message = str(exc)[:2000]
            log.save(update_fields=["status", "error_message"])
            return log

    @staticmethod
    def retry_email(email_log_id: int, *, sent_by_id: int | None = None) -> EmailLog:
        """Ponow wysylke dla nieudanego logu (nowy EmailLog przy force_resend)."""
        failed_log = (
            EmailLog.objects.select_related("document").filter(pk=email_log_id).first()
        )
        if failed_log is None:
            raise ValidationError(f"Log email {email_log_id} nie istnieje.")
        if failed_log.status != EmailStatus.FAILED:
            raise ValidationError("Mozna ponowic tylko wysylke ze statusem failed.")
        return EmailService.send_document_email(
            failed_log.document_id,
            sent_by_id=sent_by_id,
            force_resend=True,
        )
