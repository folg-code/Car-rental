from __future__ import annotations

from uuid import UUID

from django.contrib.auth.models import AbstractBaseUser

from apps.bookings.models import Customer, Reservation
from apps.documents.models import Document
from apps.documents.selectors.document import get_document_for_customer
from apps.website.selectors.customer_portal import (
    get_portal_customer,
    get_portal_reservation,
    list_portal_documents,
    list_portal_reservations,
)


class CustomerPortalService:
    @staticmethod
    def resolve_customer(user: AbstractBaseUser) -> Customer | None:
        if not user.is_authenticated:
            return None
        return get_portal_customer(user.pk)

    @staticmethod
    def list_reservations(*, customer_id: int) -> list[Reservation]:
        return list_portal_reservations(customer_id=customer_id)

    @staticmethod
    def get_reservation(
        *,
        reservation_id: int,
        customer_id: int,
    ) -> Reservation | None:
        return get_portal_reservation(
            reservation_id=reservation_id,
            customer_id=customer_id,
        )

    @staticmethod
    def list_documents(*, customer_id: int, limit: int = 100) -> list[Document]:
        return list_portal_documents(customer_id=customer_id, limit=limit)

    @staticmethod
    def get_downloadable_document(
        *,
        document_uuid: UUID,
        customer_id: int,
    ) -> Document | None:
        document = get_document_for_customer(document_uuid, customer_id=customer_id)
        if document is None or not document.file:
            return None
        return document
