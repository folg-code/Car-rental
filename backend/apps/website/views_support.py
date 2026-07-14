from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.permissions import staff_required
from apps.website.selectors.chat_support import (
    get_chat_session_detail,
    list_chat_sessions,
)


@staff_required
def chat_session_list(request: HttpRequest) -> HttpResponse:
    """Lista sesji czatu AI dla supportu (Sprint 8b)."""
    return render(
        request,
        "website/support/chat_session_list.html",
        {"sessions": list_chat_sessions(limit=100)},
    )


@staff_required
def chat_session_detail(request: HttpRequest, session_id: int) -> HttpResponse:
    """Podglad wiadomosci w sesji czatu."""
    session = get_chat_session_detail(session_id)
    if session is None:
        return redirect("website_support:session_list")
    return render(
        request,
        "website/support/chat_session_detail.html",
        {
            "session": session,
            "messages": session.messages.order_by("created_at"),
        },
    )
