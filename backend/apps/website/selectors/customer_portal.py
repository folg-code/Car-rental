from __future__ import annotations

from apps.bookings.models import Customer, Reservation
from apps.bookings.selectors.customer import get_customer_by_user_id
from apps.bookings.selectors.reservation import get_reservation_by_id, list_reservations
from apps.documents.models import Document
from apps.documents.selectors.document import list_documents


def get_portal_customer(user_id: int) -> Customer | None:
    return get_customer_by_user_id(user_id)


def list_portal_reservations(*, customer_id: int) -> list[Reservation]:
    return list(list_reservations(customer_id=customer_id))


def get_portal_reservation(
    *,
    reservation_id: int,
    customer_id: int,
) -> Reservation | None:
    reservation = get_reservation_by_id(reservation_id)
    if reservation is None or reservation.customer_id != customer_id:
        return None
    return reservation


def list_portal_documents(*, customer_id: int, limit: int = 100) -> list[Document]:
    return list(list_documents(customer_id=customer_id, limit=limit))
