import pytest

from apps.documents.tasks import ping


@pytest.mark.django_db
def test_celery_ping_runs_eager() -> None:
    result = ping.delay()
    assert result.get(timeout=1) == "pong"
