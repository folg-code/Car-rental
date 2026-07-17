from __future__ import annotations

import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from apps.bookings.constants import (
    RESERVATION_EMAIL_CONFIRMED,
    RESERVATION_EMAIL_PENDING,
    RESERVATION_EMAIL_TEMPLATES,
)
from apps.bookings.selectors.reservation import get_reservation_by_id
from apps.bookings.services.price_snapshot import PriceSnapshotService

logger = logging.getLogger(__name__)


class ReservationEmailService:
    @staticmethod
    def enqueue_reservation_email(
        reservation_id: int,
        *,
        email_kind: str,
    ) -> None:
        from apps.bookings.tasks import send_reservation_email_task

        send_reservation_email_task.delay(reservation_id, email_kind=email_kind)

    @staticmethod
    def send_reservation_email(
        reservation_id: int,
        *,
        email_kind: str,
    ) -> bool:
        """
        Wyslij email potwierdzenia rezerwacji.

        Blad wysylki nie propaguje wyjatku — log w loggerze.
        """
        templates = RESERVATION_EMAIL_TEMPLATES.get(email_kind)
        if templates is None:
            raise ValidationError(f"Nieznany typ emaila rezerwacji: {email_kind}")

        reservation = get_reservation_by_id(reservation_id)
        if reservation is None:
            logger.warning(
                "Reservation email skipped — reservation %s not found",
                reservation_id,
            )
            return False

        recipient = (reservation.customer.email or "").strip()
        if not recipient:
            logger.info(
                "Reservation email skipped — no email for reservation %s",
                reservation_id,
            )
            return False

        context = ReservationEmailService._build_context(
            reservation,
            email_kind=email_kind,
        )
        subject = render_to_string(templates["subject"], context).strip()
        text_body = render_to_string(templates["text"], context)
        html_body = render_to_string(templates["html"], context)

        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
            )
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=False)
        except Exception:
            logger.exception(
                "Reservation email failed for reservation %s (%s)",
                reservation_id,
                email_kind,
            )
            return False

        return True

    @staticmethod
    def _build_context(reservation, *, email_kind: str) -> dict:
        base_url = settings.PUBLIC_SITE_BASE_URL.rstrip("/")
        payment_path = reverse(
            "website:start_payment",
            kwargs={"reservation_id": reservation.pk},
        )
        confirmation_path = reverse(
            "website:booking_confirmation_by_id",
            kwargs={"reservation_id": reservation.pk},
        )
        total = PriceSnapshotService.reservation_total(reservation)
        portal_path = reverse("customer_portal:home")
        otp_login_path = reverse("customer_portal:otp_request")
        deposit = reservation.car.category.deposit
        return {
            "customer_name": reservation.customer.first_name,
            "reservation_id": reservation.pk,
            "status_display": reservation.get_status_display(),
            "car_label": f"{reservation.car.make} {reservation.car.model}",
            "registration_number": reservation.car.registration_number,
            "category_name": reservation.car.category.name,
            "start_at": reservation.start_at,
            "end_at": reservation.end_at,
            "total_amount": total,
            "deposit_amount": deposit,
            "payment_url": urljoin(f"{base_url}/", payment_path.lstrip("/")),
            "confirmation_url": urljoin(
                f"{base_url}/",
                confirmation_path.lstrip("/"),
            ),
            "portal_url": urljoin(f"{base_url}/", portal_path.lstrip("/")),
            "portal_login_url": urljoin(f"{base_url}/", otp_login_path.lstrip("/")),
            "is_confirmed": email_kind == RESERVATION_EMAIL_CONFIRMED,
            "is_pending_payment": email_kind == RESERVATION_EMAIL_PENDING,
        }
