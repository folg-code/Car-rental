from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from apps.website.models import ChatMessage, ChatSession


@dataclass(frozen=True, slots=True)
class ChatPurgeResult:
    messages_deleted: int
    sessions_deleted: int
    retention_days: int
    dry_run: bool


class ChatRetentionService:
    """Retencja wiadomosci czatu (Sprint 8b — RODO)."""

    @staticmethod
    def purge_old_data(
        retention_days: int,
        *,
        dry_run: bool = False,
    ) -> ChatPurgeResult:
        if retention_days < 1:
            msg = "Retencja musi wynosic co najmniej 1 dzien."
            raise ValueError(msg)

        cutoff = timezone.now() - timedelta(days=retention_days)
        old_messages = ChatMessage.objects.filter(created_at__lt=cutoff)
        messages_deleted = old_messages.count()

        if not dry_run and messages_deleted:
            old_messages.delete()

        empty_sessions = ChatSession.objects.filter(messages__isnull=True)
        sessions_deleted = empty_sessions.count()

        if not dry_run and sessions_deleted:
            empty_sessions.delete()

        return ChatPurgeResult(
            messages_deleted=messages_deleted,
            sessions_deleted=sessions_deleted,
            retention_days=retention_days,
            dry_run=dry_run,
        )
