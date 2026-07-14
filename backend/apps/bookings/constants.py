from __future__ import annotations

RESERVATION_EMAIL_PENDING = "pending_payment"
RESERVATION_EMAIL_CONFIRMED = "confirmed"

RESERVATION_EMAIL_TEMPLATES: dict[str, dict[str, str]] = {
    RESERVATION_EMAIL_PENDING: {
        "subject": "bookings/email/reservation_pending_subject.txt",
        "text": "bookings/email/reservation_pending_body.txt",
        "html": "bookings/email/reservation_pending_body.html",
    },
    RESERVATION_EMAIL_CONFIRMED: {
        "subject": "bookings/email/reservation_confirmed_subject.txt",
        "text": "bookings/email/reservation_confirmed_body.txt",
        "html": "bookings/email/reservation_confirmed_body.html",
    },
}
