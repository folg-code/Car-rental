from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from apps.bookings.constants import RESERVATION_SMS_TEMPLATES
from apps.bookings.selectors.reservation import get_reservation_by_id
from apps.bookings.services.reservation_email import ReservationEmailService
from apps.notifications.models import SmsStatus
from apps.notifications.services.sms_delivery import SmsDeliveryService

logger = logging.getLogger(__name__)


class ReservationSmsService:
    @staticmethod
    def enqueue_reservation_sms(
        reservation_id: int,
        *,
        sms_kind: str,
    ) -> None:
        from apps.bookings.tasks import send_reservation_sms_task

        send_reservation_sms_task.delay(reservation_id, sms_kind=sms_kind)

    @staticmethod
    def send_reservation_sms(
        reservation_id: int,
        *,
        sms_kind: str,
    ) -> bool:
        """
        Wyslij SMS potwierdzenia rezerwacji.

        Blad wysylki nie propaguje wyjatku — log w SmsLog / loggerze.
        """
        template_path = RESERVATION_SMS_TEMPLATES.get(sms_kind)
        if template_path is None:
            raise ValidationError(f"Nieznany typ SMS rezerwacji: {sms_kind}")

        reservation = get_reservation_by_id(reservation_id)
        if reservation is None:
            logger.warning(
                "Reservation SMS skipped — reservation %s not found",
                reservation_id,
            )
            return False

        recipient = (reservation.customer.phone or "").strip()
        if not recipient:
            logger.info(
                "Reservation SMS skipped — no phone for reservation %s",
                reservation_id,
            )
            return False

        context = ReservationEmailService._build_context(
            reservation,
            email_kind=sms_kind,
        )
        body = render_to_string(template_path, context).strip()

        log = SmsDeliveryService.send(
            recipient,
            body,
            reservation_id=reservation_id,
        )
        return log.status == SmsStatus.SENT
