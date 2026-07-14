from celery import shared_task

from apps.documents.services.email import EmailService


@shared_task(name="documents.ping")
def ping() -> str:
    """Health-check task for Celery worker wiring (task 9.7)."""
    return "pong"


@shared_task(name="documents.send_document_email")
def send_document_email_task(
    document_id: int,
    sent_by_id: int | None = None,
) -> int | None:
    """Wyslij PDF dokumentu w tle (task 9.8)."""
    log = EmailService.send_document_email(
        document_id,
        sent_by_id=sent_by_id,
    )
    return log.pk if log is not None else None
