import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.website.adapters.llm import LLMResponse
from apps.website.models import ChatMessage, ChatMessageRole, ChatSession
from apps.website.services.consultant_chat import ConsultantChatService


class StubLLMClient:
    def complete(self, messages, *, max_tokens=None):
        del max_tokens
        return LLMResponse(content="Stub odpowiedz asystenta.")


@pytest.mark.django_db
class TestConsultantChatService:
    def setup_method(self) -> None:
        cache.clear()

    def test_send_message_creates_session_and_messages(self) -> None:
        assistant = ConsultantChatService.send_message(
            "",
            "Jak zarezerwowac auto?",
            client_ip="127.0.0.1",
            llm_client=StubLLMClient(),
        )
        assert assistant.role == ChatMessageRole.ASSISTANT
        assert assistant.content == "Stub odpowiedz asystenta."
        assert ChatSession.objects.count() == 1
        assert ChatMessage.objects.filter(role=ChatMessageRole.USER).count() == 1

    def test_reuses_existing_session(self) -> None:
        session = ChatSession.objects.create(session_key="existing-key")
        ConsultantChatService.send_message(
            "existing-key",
            "Pierwsze pytanie",
            client_ip="127.0.0.1",
            llm_client=StubLLMClient(),
        )
        ConsultantChatService.send_message(
            "existing-key",
            "Drugie pytanie",
            client_ip="127.0.0.1",
            llm_client=StubLLMClient(),
        )
        session.refresh_from_db()
        assert session.messages.count() == 4

    def test_rejects_empty_message(self) -> None:
        with pytest.raises(ValidationError, match="pusta"):
            ConsultantChatService.send_message(
                "key-1",
                "   ",
                client_ip="127.0.0.1",
                llm_client=StubLLMClient(),
            )

    @override_settings(CHAT_RATE_LIMIT_PER_HOUR=2)
    def test_rate_limit_blocks_excess_messages(self) -> None:
        for _ in range(2):
            ConsultantChatService.send_message(
                "rate-key",
                "Pytanie testowe",
                client_ip="10.0.0.1",
                llm_client=StubLLMClient(),
            )
        with pytest.raises(ValidationError, match="limit"):
            ConsultantChatService.send_message(
                "rate-key",
                "Trzecie pytanie",
                client_ip="10.0.0.1",
                llm_client=StubLLMClient(),
            )
