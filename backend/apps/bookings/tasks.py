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
