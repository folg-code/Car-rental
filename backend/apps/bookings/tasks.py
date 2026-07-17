from celery import shared_task


@shared_task(name="bookings.send_reservation_email")
def send_reservation_email_task(
    reservation_id: int,
    *,
    email_kind: str,
) -> bool:
    """Wyslij email potwierdzenia rezerwacji w tle."""
    from apps.bookings.services.reservation_email import ReservationEmailService

    return ReservationEmailService.send_reservation_email(
        reservation_id,
        email_kind=email_kind,
    )


@shared_task(name="bookings.send_portal_login_code")
def send_portal_login_code_task(customer_id: int, code: str) -> bool:
    """Wyslij kod OTP do logowania w portalu klienta (Sprint 12.2)."""
    from apps.website.services.portal_auth import PortalLoginService

    return PortalLoginService.send_login_code_email(
        customer_id=customer_id,
        code=code,
    )


@shared_task(name="bookings.send_reservation_sms")
def send_reservation_sms_task(
    reservation_id: int,
    *,
    sms_kind: str,
) -> bool:
    """Wyslij SMS potwierdzenia rezerwacji w tle."""
    from apps.bookings.services.reservation_sms import ReservationSmsService

    return ReservationSmsService.send_reservation_sms(
        reservation_id,
        sms_kind=sms_kind,
    )
