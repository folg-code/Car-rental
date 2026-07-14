from __future__ import annotations

import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.website.adapters.llm import LLMClient, get_llm_client
from apps.website.faq_content import build_faq_context
from apps.website.models import ChatMessage, ChatMessageRole, ChatSession
from apps.website.services.chat_tool_router import ChatToolRouter
from apps.website.services.chat_tools import format_tool_results

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

MAX_HISTORY_MESSAGES = 20
CHAT_SESSION_COOKIE = "chat_session_id"

SYSTEM_PROMPT = """\
Jestes asystentem wypozyczalni samochodow. Odpowiadaj po polsku, krotko i rzeczowo.

ZASADY:
- Nie tworz rezerwacji ani platnosci — kieruj klienta do formularza online.
- Nie podawaj danych innych klientow.
- Nie pros o numer PESEL ani wrazliwe dane osobowe.
- Przy orientacyjnych cenach dodaj disclaimer, ze wiazaca jest dopiero rezerwacja.

{faq}
"""


class ConsultantChatService:
    """Orkiestracja czatu z asystentem AI (Sprint 8b)."""

    @staticmethod
    def get_or_create_session(
        session_key: str | None,
        *,
        user: AbstractBaseUser | None = None,
    ) -> tuple[ChatSession, str]:
        key = (session_key or "").strip()
        if not key:
            key = ChatSession.generate_session_key()
            session = ChatSession.objects.create(session_key=key, user=user)
            return session, key

        session, created = ChatSession.objects.get_or_create(
            session_key=key,
            defaults={"user": user},
        )
        if user is not None and session.user_id is None:
            session.user = user
            session.save(update_fields=["user", "updated_at"])
        return session, key

    @staticmethod
    def check_rate_limit(*, session_key: str, client_ip: str) -> None:
        hour_bucket = int(time.time() // 3600)
        limit = settings.CHAT_RATE_LIMIT_PER_HOUR
        for key in (
            f"chat_rate:session:{session_key}:{hour_bucket}",
            f"chat_rate:ip:{client_ip}:{hour_bucket}",
        ):
            count = cache.get(key, 0)
            if count >= limit:
                raise ValidationError(
                    "Przekroczono limit wiadomosci. Sprobuj ponownie pozniej.",
                )

    @staticmethod
    def _increment_rate_limit(*, session_key: str, client_ip: str) -> None:
        hour_bucket = int(time.time() // 3600)
        ttl = 3600
        for key in (
            f"chat_rate:session:{session_key}:{hour_bucket}",
            f"chat_rate:ip:{client_ip}:{hour_bucket}",
        ):
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, timeout=ttl)

    @staticmethod
    def _build_llm_messages(session: ChatSession) -> list[dict[str, str]]:
        system_content = SYSTEM_PROMPT.format(faq=build_faq_context())
        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        history = session.messages.order_by("-created_at")[:MAX_HISTORY_MESSAGES]
        for message in reversed(list(history)):
            if message.role in {ChatMessageRole.USER, ChatMessageRole.ASSISTANT}:
                messages.append({"role": message.role, "content": message.content})
        return messages

    @staticmethod
    @transaction.atomic
    def send_message(
        session_key: str,
        content: str,
        *,
        client_ip: str = "",
        user: AbstractBaseUser | None = None,
        llm_client: LLMClient | None = None,
    ) -> ChatMessage:
        text = content.strip()
        if not text:
            raise ValidationError("Wiadomosc nie moze byc pusta.")
        if len(text) > 4000:
            raise ValidationError("Wiadomosc jest zbyt dluga.")

        session, key = ConsultantChatService.get_or_create_session(
            session_key,
            user=user,
        )
        ConsultantChatService.check_rate_limit(session_key=key, client_ip=client_ip)

        ChatMessage.objects.create(
            session=session,
            role=ChatMessageRole.USER,
            content=text,
        )

        client = llm_client or get_llm_client()
        tool_results = ChatToolRouter.run_for_message(text, user=user)
        if tool_results:
            reply = format_tool_results(tool_results)
        else:
            llm_messages = ConsultantChatService._build_llm_messages(session)
            response = client.complete(llm_messages)
            reply = response.content.strip()

        assistant_message = ChatMessage.objects.create(
            session=session,
            role=ChatMessageRole.ASSISTANT,
            content=reply,
        )
        session.save(update_fields=["updated_at"])
        ConsultantChatService._increment_rate_limit(
            session_key=key, client_ip=client_ip
        )
        return assistant_message
