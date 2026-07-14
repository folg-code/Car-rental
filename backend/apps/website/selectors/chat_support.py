from __future__ import annotations

from django.db.models import Count, QuerySet

from apps.website.models import ChatSession


def list_chat_sessions(*, limit: int = 50) -> QuerySet[ChatSession]:
    return (
        ChatSession.objects.select_related("user")
        .annotate(message_count=Count("messages"))
        .order_by("-updated_at")[:limit]
    )


def get_chat_session_detail(session_id: int) -> ChatSession | None:
    return (
        ChatSession.objects.select_related("user")
        .prefetch_related("messages")
        .filter(pk=session_id)
        .first()
    )
