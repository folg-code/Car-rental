from unittest.mock import patch

import pytest

from apps.documents.services.document_sms import DocumentSmsService
from apps.documents.services.email import EmailService
from apps.documents.tasks import send_document_sms_task
from apps.notifications.models import SmsLog, SmsStatus


@pytest.fixture(autouse=True)
def sms_settings(settings) -> None:
    settings.SMS_ENABLED = True
    settings.SMS_PROVIDER = "mock"
    settings.SMS_FROM_NUMBER = "+48111111111"
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.mark.django_db
class TestSendDocumentSmsTask:
    def test_task_sends_sms(self, handover_document) -> None:
        handover_document.customer.phone = "+48111222333"
        handover_document.customer.save(update_fields=["phone"])

        log_id = send_document_sms_task(handover_document.pk)
        assert log_id is not None
        log = handover_document.sms_logs.get(pk=log_id)
        assert log.status == SmsStatus.SENT
        assert "protokol wydania" in log.body.lower()

    def test_enqueue_dispatches_celery_task(self, handover_document) -> None:
        with patch(
            "apps.documents.tasks.send_document_sms_task.delay",
        ) as mock_delay:
            DocumentSmsService.enqueue_document_sms(handover_document.pk, sent_by_id=7)
        mock_delay.assert_called_once_with(handover_document.pk, sent_by_id=7)

    def test_skips_when_no_phone(self, handover_document) -> None:
        handover_document.customer.phone = ""
        handover_document.customer.save(update_fields=["phone"])

        log = DocumentSmsService.send_document_sms(handover_document.pk)
        assert log is not None
        assert log.status == SmsStatus.FAILED
        assert "telefonu" in log.error_message.lower()

    def test_pdf_generation_enqueues_sms(self, handover_document) -> None:
        handover_document.customer.phone = "+48111222333"
        handover_document.customer.save(update_fields=["phone"])
        SmsLog.objects.all().delete()

        with patch(
            "apps.documents.tasks.send_document_sms_task.delay",
        ) as mock_delay:
            EmailService.enqueue_document_email(handover_document.pk)
            DocumentSmsService.enqueue_document_sms(handover_document.pk)

        mock_delay.assert_called_once_with(handover_document.pk, sent_by_id=None)
