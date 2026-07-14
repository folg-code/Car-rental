from datetime import timedelta

import pytest
from django.utils import timezone

from apps.website.models import ChatMessage, ChatMessageRole, ChatSession
from apps.website.services.chat_retention import ChatRetentionService


@pytest.mark.django_db
class TestChatRetentionService:
    def test_purge_deletes_old_messages_and_empty_sessions(self) -> None:
        session = ChatSession.objects.create(session_key="old-session")
        ChatMessage.objects.create(
            session=session,
            role=ChatMessageRole.USER,
            content="Stara wiadomosc",
        )
        ChatMessage.objects.filter(pk=session.messages.first().pk).update(
            created_at=timezone.now() - timedelta(days=100),
        )

        fresh_session = ChatSession.objects.create(session_key="fresh-session")
        ChatMessage.objects.create(
            session=fresh_session,
            role=ChatMessageRole.USER,
            content="Swieza wiadomosc",
        )

        result = ChatRetentionService.purge_old_data(90, dry_run=False)

        assert result.messages_deleted == 1
        assert result.sessions_deleted == 1
        assert ChatSession.objects.filter(session_key="fresh-session").exists()
        assert not ChatSession.objects.filter(session_key="old-session").exists()
        assert fresh_session.messages.count() == 1

    def test_dry_run_does_not_delete(self) -> None:
        session = ChatSession.objects.create(session_key="dry-run")
        ChatMessage.objects.create(
            session=session,
            role=ChatMessageRole.USER,
            content="Test",
        )
        ChatMessage.objects.filter(pk=session.messages.first().pk).update(
            created_at=timezone.now() - timedelta(days=120),
        )

        result = ChatRetentionService.purge_old_data(90, dry_run=True)

        assert result.messages_deleted == 1
        assert result.dry_run is True
        assert session.messages.count() == 1

    def test_rejects_invalid_retention(self) -> None:
        with pytest.raises(ValueError, match="1 dzien"):
            ChatRetentionService.purge_old_data(0)
