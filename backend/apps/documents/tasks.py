from celery import shared_task


@shared_task(name="documents.ping")
def ping() -> str:
    """Health-check task for Celery worker wiring (task 9.7)."""
    return "pong"
