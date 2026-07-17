from unittest.mock import patch

import pytest
from django.core import mail

from apps.documents.models import EmailStatus
from apps.documents.services.email import EmailService
from apps.documents.tasks import (
    DocumentEmailSendError,
    retry_failed_document_email_task,
    send_document_email_task,
)


@pytest.mark.django_db
class TestSendDocumentEmailTask:
    def test_task_sends_email(self, handover_document) -> None:
        log_id = send_document_email_task.run(handover_document.pk)
        assert log_id is not None
        log = handover_document.email_logs.get(pk=log_id)
        assert log.status == EmailStatus.SENT
        assert len(mail.outbox) == 1

    def test_enqueue_dispatches_celery_task(self, handover_document) -> None:
        with patch(
            "apps.documents.tasks.send_document_email_task.delay",
        ) as mock_delay:
            EmailService.enqueue_document_email(handover_document.pk, sent_by_id=7)
        mock_delay.assert_called_once_with(handover_document.pk, sent_by_id=7)

    def test_task_retries_on_transient_failure(self, handover_document) -> None:
        handover_document.email_logs.all().delete()
        with patch(
            "apps.documents.services.email.EmailMultiAlternatives.send",
            side_effect=ConnectionError("SMTP down"),
        ):
            with pytest.raises(DocumentEmailSendError, match="SMTP down"):
                send_document_email_task.run(handover_document.pk)

        failed = handover_document.email_logs.filter(status=EmailStatus.FAILED).first()
        assert failed is not None
        assert "SMTP down" in failed.error_message

    def test_task_does_not_retry_missing_email(self, handover_document) -> None:
        from apps.bookings.models import Customer

        handover_document.email_logs.all().delete()
        Customer.objects.filter(pk=handover_document.customer_id).update(email="")

        log_id = send_document_email_task.run(handover_document.pk)
        assert log_id is not None
        log = handover_document.email_logs.get(pk=log_id)
        assert log.status == EmailStatus.FAILED
        assert log.error_message == "Klient nie ma adresu email."

    def test_retry_failed_task(self, handover_document) -> None:
        with patch(
            "apps.documents.services.email.EmailMultiAlternatives.send",
            side_effect=ConnectionError("SMTP down"),
        ):
            failed = EmailService.send_document_email(
                handover_document.pk,
                force_resend=True,
            )
        assert failed.status == EmailStatus.FAILED

        mail.outbox.clear()
        new_id = retry_failed_document_email_task.run(failed.pk)
        new_log = handover_document.email_logs.get(pk=new_id)
        assert new_log.status == EmailStatus.SENT
        assert len(mail.outbox) == 1
