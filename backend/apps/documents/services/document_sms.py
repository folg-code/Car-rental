from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from apps.documents.constants import SMS_TEMPLATES_BY_DOCUMENT_TYPE
from apps.documents.services.email import EmailService
from apps.notifications.models import SmsStatus
from apps.notifications.services.sms_delivery import SmsDeliveryService

logger = logging.getLogger(__name__)


class DocumentSmsService:
    @staticmethod
    def enqueue_document_sms(
        document_id: int,
        *,
        sent_by_id: int | None = None,
    ) -> None:
        from apps.documents.tasks import send_document_sms_task

        send_document_sms_task.delay(document_id, sent_by_id=sent_by_id)

    @staticmethod
    def send_document_sms(
        document_id: int,
        *,
        sent_by_id: int | None = None,
        force_resend: bool = False,
    ):
        """
        Wyslij SMS z informacja o protokole (bez PDF).

        Blad wysylki nie propaguje wyjatku — status w SmsLog.
        """
        from apps.notifications.models import SmsLog

        document = EmailService._get_document(document_id)
        recipient = (document.customer.phone or "").strip()
        if not recipient:
            return SmsLog.objects.create(
                document=document,
                recipient_phone="",
                body=document.title[:500],
                status=SmsStatus.FAILED,
                error_message="Klient nie ma numeru telefonu.",
                sent_by_id=sent_by_id,
            )

        if not force_resend:
            existing = (
                document.sms_logs.filter(
                    recipient_phone=recipient,
                    status=SmsStatus.SENT,
                )
                .order_by("-sent_at")
                .first()
            )
            if existing is not None:
                return existing

        template_path = SMS_TEMPLATES_BY_DOCUMENT_TYPE.get(document.document_type)
        if template_path is None:
            logger.info(
                "Document SMS skipped — no template for type %s",
                document.document_type,
            )
            return None

        context = EmailService._build_context(document)
        body = render_to_string(template_path, context).strip()

        return SmsDeliveryService.send(
            recipient,
            body,
            document_id=document_id,
            sent_by_id=sent_by_id,
        )

    @staticmethod
    def retry_sms(sms_log_id: int, *, sent_by_id: int | None = None):
        from apps.notifications.models import SmsLog

        failed_log = (
            SmsLog.objects.select_related("document").filter(pk=sms_log_id).first()
        )
        if failed_log is None:
            raise ValidationError(f"Log SMS {sms_log_id} nie istnieje.")
        if failed_log.status != SmsStatus.FAILED:
            raise ValidationError("Mozna ponowic tylko wysylke ze statusem failed.")
        if failed_log.document_id is None:
            raise ValidationError("Log SMS nie jest powiazany z dokumentem.")
        return DocumentSmsService.send_document_sms(
            failed_log.document_id,
            sent_by_id=sent_by_id,
            force_resend=True,
        )
