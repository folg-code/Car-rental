from unittest.mock import patch

import pytest
from django.core import mail

from apps.documents.models import EmailStatus
from apps.documents.services.email import EmailService
from apps.documents.tasks import send_document_email_task


@pytest.mark.django_db
class TestSendDocumentEmailTask:
    def test_task_sends_email(self, handover_document) -> None:
        log_id = send_document_email_task(handover_document.pk)
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
