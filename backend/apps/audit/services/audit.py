from __future__ import annotations

import logging
from typing import Any

from apps.audit.models import AuditAction, AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def log(
        action: str,
        *,
        actor_id: int | None = None,
        reservation_id: int | None = None,
        rental_id: int | None = None,
        payment_id: int | None = None,
        object_type: str = "",
        object_id: int | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog | None:
        try:
            return AuditLog.objects.create(
                action=action,
                actor_id=actor_id,
                reservation_id=reservation_id,
                rental_id=rental_id,
                payment_id=payment_id,
                object_type=object_type,
                object_id=object_id,
                old_value=old_value,
                new_value=new_value,
                metadata=metadata or {},
            )
        except Exception:
            logger.exception("Nie udalo sie zapisac audytu: %s", action)
            return None

    @staticmethod
    def log_status_change(
        action: str,
        *,
        actor_id: int | None = None,
        reservation_id: int | None = None,
        rental_id: int | None = None,
        old_status: str,
        new_status: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog | None:
        return AuditService.log(
            action,
            actor_id=actor_id,
            reservation_id=reservation_id,
            rental_id=rental_id,
            old_value={"status": old_status},
            new_value={"status": new_status},
            metadata=metadata,
        )

    @staticmethod
    def log_payment(
        payment,
        *,
        actor_id: int | None = None,
    ) -> AuditLog | None:
        return AuditService.log(
            AuditAction.PAYMENT_RECORDED,
            actor_id=actor_id or payment.recorded_by_id,
            reservation_id=payment.reservation_id,
            rental_id=payment.rental_id,
            payment_id=payment.pk,
            metadata={
                "payment_type": payment.payment_type,
                "method": payment.method,
                "amount": str(payment.amount),
            },
        )
