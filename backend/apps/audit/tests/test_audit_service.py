import pytest

from apps.audit.models import AuditAction, AuditLog
from apps.audit.services.audit import AuditService


@pytest.mark.django_db
class TestAuditService:
    def test_log_creates_append_only_row(self) -> None:
        entry = AuditService.log(
            AuditAction.RESERVATION_CONFIRMED,
            old_value={"status": "draft"},
            new_value={"status": "confirmed"},
        )
        assert entry is not None
        assert AuditLog.objects.count() == 1

    def test_audit_log_cannot_be_updated(self) -> None:
        entry = AuditService.log(
            AuditAction.RENTAL_STARTED,
            old_value={"status": "scheduled"},
            new_value={"status": "active"},
        )
        assert entry is not None
        entry.metadata = {"changed": True}
        with pytest.raises(ValueError, match="nie moze byc modyfikowany"):
            entry.save()
