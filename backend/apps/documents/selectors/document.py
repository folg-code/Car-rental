from __future__ import annotations

from uuid import UUID

from django.db.models import Prefetch, QuerySet

from apps.documents.models import Document, DocumentType, EmailLog


def _document_queryset() -> QuerySet[Document]:
    return Document.objects.select_related(
        "rental",
        "rental__reservation",
        "rental__reservation__customer",
        "rental__reservation__car",
        "customer",
    ).prefetch_related(
        Prefetch(
            "email_logs",
            queryset=EmailLog.objects.order_by("-created_at"),
        ),
    )


def list_documents(
    *,
    rental_id: int | None = None,
    limit: int = 100,
) -> QuerySet[Document]:
    qs = _document_queryset().order_by("-generated_at")
    if rental_id is not None:
        qs = qs.filter(rental_id=rental_id)
    return qs[:limit]


def get_document_by_uuid(document_uuid: UUID) -> Document | None:
    return _document_queryset().filter(uuid=document_uuid).first()


def get_handover_protocol_document(handover_protocol_id: int) -> Document | None:
    return (
        _document_queryset()
        .filter(
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            handover_protocol_id=handover_protocol_id,
        )
        .order_by("-version")
        .first()
    )


def get_return_protocol_document(return_protocol_id: int) -> Document | None:
    return (
        _document_queryset()
        .filter(
            document_type=DocumentType.RETURN_PROTOCOL_PDF,
            return_protocol_id=return_protocol_id,
        )
        .order_by("-version")
        .first()
    )
