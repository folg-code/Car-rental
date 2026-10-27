from celery import shared_task

from apps.documents.models import EmailStatus
from apps.documents.services.email import EmailService

_PERMANENT_EMAIL_ERRORS = ("Klient nie ma adresu email.",)


class DocumentEmailSendError(Exception):
    """Transient document email failure — Celery may retry."""


@shared_task(name="documents.ping")
def ping() -> str:
    """Health-check task for Celery worker wiring (task 9.7)."""
    return "pong"


@shared_task(
    bind=True,
    name="documents.send_document_email",
    autoretry_for=(DocumentEmailSendError,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def send_document_email_task(
    self,
    document_id: int,
    sent_by_id: int | None = None,
) -> int | None:
    """Wyslij PDF dokumentu w tle; przy bledzie SMTP retry Celery (Sprint 12.5)."""
    log = EmailService.send_document_email(
        document_id,
        sent_by_id=sent_by_id,
    )
    if log is None:
        return None
    if log.status == EmailStatus.FAILED:
        error = (log.error_message or "").strip()
        if error in _PERMANENT_EMAIL_ERRORS:
            return log.pk
        raise DocumentEmailSendError(error or "Document email send failed")
    return log.pk


@shared_task(name="documents.retry_failed_document_email")
def retry_failed_document_email_task(
    email_log_id: int,
    sent_by_id: int | None = None,
) -> int:
    """Ponow wysylke nieudanego EmailLog (admin / reczna kolejka)."""
    log = EmailService.retry_email(email_log_id, sent_by_id=sent_by_id)
    return log.pk


@shared_task(name="documents.send_document_sms")
def send_document_sms_task(
    document_id: int,
    sent_by_id: int | None = None,
) -> int | None:
    """Wyslij SMS o protokole w tle."""
    from apps.documents.services.document_sms import DocumentSmsService

    log = DocumentSmsService.send_document_sms(
        document_id,
        sent_by_id=sent_by_id,
    )
    return log.pk if log is not None else None
