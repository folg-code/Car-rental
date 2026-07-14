from __future__ import annotations

import logging

from django.conf import settings
from django.utils import timezone

from apps.notifications.adapters.sms import get_sms_client
from apps.notifications.models import SmsLog, SmsStatus

logger = logging.getLogger(__name__)


class SmsDeliveryService:
    @staticmethod
    def send(
        phone: str,
        body: str,
        *,
        reservation_id: int | None = None,
        document_id: int | None = None,
        sent_by_id: int | None = None,
    ) -> SmsLog:
        recipient = phone.strip()
        if not settings.SMS_ENABLED:
            return SmsLog.objects.create(
                reservation_id=reservation_id,
                document_id=document_id,
                recipient_phone=recipient,
                body=body,
                status=SmsStatus.SKIPPED,
                error_message="SMS wylaczone (SMS_ENABLED=False).",
                sent_by_id=sent_by_id,
            )

        log = SmsLog.objects.create(
            reservation_id=reservation_id,
            document_id=document_id,
            recipient_phone=recipient,
            body=body,
            status=SmsStatus.PENDING,
            sent_by_id=sent_by_id,
        )

        try:
            client = get_sms_client()
            result = client.send_message(
                to=recipient,
                body=body,
                from_number=settings.SMS_FROM_NUMBER,
            )
            log.status = SmsStatus.SENT
            log.external_id = result.external_id
            log.sent_at = timezone.now()
            log.error_message = ""
            log.save(
                update_fields=["status", "external_id", "sent_at", "error_message"],
            )
        except Exception as exc:
            logger.exception("SMS send failed to %s", recipient)
            log.status = SmsStatus.FAILED
            log.error_message = str(exc)[:2000]
            log.save(update_fields=["status", "error_message"])

        return log
