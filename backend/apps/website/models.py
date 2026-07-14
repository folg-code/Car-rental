from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    """Sesja czatu z asystentem AI (anonimowa lub powiazana z uzytkownikiem)."""

    session_key = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "sesja czatu"
        verbose_name_plural = "sesje czatu"

    def __str__(self) -> str:
        return f"ChatSession {self.session_key[:8]}…"

    @classmethod
    def generate_session_key(cls) -> str:
        return uuid.uuid4().hex


class ChatMessageRole(models.TextChoices):
    USER = "user", "Uzytkownik"
    ASSISTANT = "assistant", "Asystent"
    SYSTEM = "system", "System"


class ChatMessage(models.Model):
    """Pojedyncza wiadomosc w sesji czatu."""

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=ChatMessageRole.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "wiadomosc czatu"
        verbose_name_plural = "wiadomosci czatu"

    def __str__(self) -> str:
        preview = self.content[:40].replace("\n", " ")
        return f"{self.role}: {preview}"
