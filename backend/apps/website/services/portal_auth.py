from __future__ import annotations

import hashlib
import logging
import secrets
import time

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.bookings.models import Customer, Reservation
from apps.bookings.selectors.customer import get_customer_by_email
from apps.bookings.services.customer import CustomerService

logger = logging.getLogger(__name__)

PORTAL_OTP_TTL_SECONDS = 600
PORTAL_OTP_RATE_LIMIT = 5
PORTAL_OTP_RATE_WINDOW_SECONDS = 3600
SESSION_CHALLENGE_KEY = "portal_otp_challenge"


class PortalLoginService:
    @staticmethod
    def request_code(*, identifier: str, client_ip: str) -> tuple[Customer, str]:
        customer = PortalLoginService._resolve_customer(identifier)
        recipient = (customer.email or "").strip()
        if not recipient:
            raise ValidationError(
                "Ten klient nie ma adresu email — nie mozna wyslac kodu."
            )

        PortalLoginService._check_rate_limit(client_ip=client_ip, email=recipient)
        code = f"{secrets.randbelow(1_000_000):06d}"
        challenge = secrets.token_urlsafe(24)
        cache.set(
            PortalLoginService._cache_key(challenge),
            {
                "customer_id": customer.pk,
                "code_hash": PortalLoginService._hash_code(code),
            },
            timeout=PORTAL_OTP_TTL_SECONDS,
        )
        PortalLoginService._increment_rate_limit(client_ip=client_ip, email=recipient)
        PortalLoginService.enqueue_login_code_email(
            customer_id=customer.pk,
            code=code,
        )
        return customer, challenge

    @staticmethod
    def verify_code(*, challenge: str, code: str):
        payload = cache.get(PortalLoginService._cache_key(challenge))
        if not payload:
            raise ValidationError("Kod wygasl lub jest nieprawidlowy. Popros o nowy.")

        attempts_key = f"portal_otp_attempts:{challenge}"
        attempts = cache.get(attempts_key, 0)
        if attempts >= 5:
            cache.delete(PortalLoginService._cache_key(challenge))
            raise ValidationError("Zbyt wiele blednych prob. Popros o nowy kod.")

        if not secrets.compare_digest(
            payload["code_hash"],
            PortalLoginService._hash_code(code.strip()),
        ):
            try:
                cache.incr(attempts_key)
            except ValueError:
                cache.set(attempts_key, 1, timeout=PORTAL_OTP_TTL_SECONDS)
            raise ValidationError("Nieprawidlowy kod logowania.")

        cache.delete(PortalLoginService._cache_key(challenge))
        cache.delete(attempts_key)
        customer = Customer.objects.filter(pk=payload["customer_id"]).first()
        if customer is None:
            raise ValidationError("Nie znaleziono klienta.")
        return CustomerService.get_or_create_portal_user(customer)

    @staticmethod
    def enqueue_login_code_email(*, customer_id: int, code: str) -> None:
        from apps.bookings.tasks import send_portal_login_code_task

        send_portal_login_code_task.delay(customer_id, code)

    @staticmethod
    def send_login_code_email(*, customer_id: int, code: str) -> bool:
        customer = Customer.objects.filter(pk=customer_id).first()
        if customer is None:
            return False
        recipient = (customer.email or "").strip()
        if not recipient:
            return False

        context = {
            "customer_name": customer.first_name,
            "code": code,
            "ttl_minutes": PORTAL_OTP_TTL_SECONDS // 60,
        }
        subject = render_to_string(
            "bookings/email/portal_login_code_subject.txt",
            context,
        ).strip()
        text_body = render_to_string(
            "bookings/email/portal_login_code_body.txt",
            context,
        )
        html_body = render_to_string(
            "bookings/email/portal_login_code_body.html",
            context,
        )
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
                "Portal login code email failed for customer %s", customer_id
            )
            return False
        return True

    @staticmethod
    def _resolve_customer(identifier: str) -> Customer:
        raw = identifier.strip()
        if not raw:
            raise ValidationError("Podaj email albo numer rezerwacji.")

        if "@" in raw:
            customer = get_customer_by_email(raw)
            if customer is None:
                raise ValidationError("Nie znaleziono klienta dla podanego emaila.")
            return customer

        if raw.isdigit():
            reservation = (
                Reservation.objects.select_related("customer")
                .filter(pk=int(raw))
                .first()
            )
            if reservation is None:
                raise ValidationError("Nie znaleziono rezerwacji o podanym numerze.")
            return reservation.customer

        raise ValidationError("Podaj poprawny email albo numer rezerwacji.")

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @staticmethod
    def _cache_key(challenge: str) -> str:
        return f"portal_otp:{challenge}"

    @staticmethod
    def _check_rate_limit(*, client_ip: str, email: str) -> None:
        hour_bucket = int(time.time() // PORTAL_OTP_RATE_WINDOW_SECONDS)
        for key in (
            f"portal_otp_rate:ip:{client_ip}:{hour_bucket}",
            f"portal_otp_rate:email:{email.lower()}:{hour_bucket}",
        ):
            if cache.get(key, 0) >= PORTAL_OTP_RATE_LIMIT:
                raise ValidationError(
                    "Przekroczono limit kodow logowania. Sprobuj ponownie pozniej."
                )

    @staticmethod
    def _increment_rate_limit(*, client_ip: str, email: str) -> None:
        hour_bucket = int(time.time() // PORTAL_OTP_RATE_WINDOW_SECONDS)
        ttl = PORTAL_OTP_RATE_WINDOW_SECONDS
        for key in (
            f"portal_otp_rate:ip:{client_ip}:{hour_bucket}",
            f"portal_otp_rate:email:{email.lower()}:{hour_bucket}",
        ):
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, timeout=ttl)
