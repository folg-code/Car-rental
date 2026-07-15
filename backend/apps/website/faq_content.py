"""Treści FAQ wykorzystywane w system prompt asystenta AI (Sprint 8b)."""

from __future__ import annotations

FAQ_ITEMS: list[dict[str, str]] = [
    {
        "question": "Jak zarezerwować auto online?",
        "answer": (
            "Sprawdź dostępność aut, zobacz orientacyjną wycenę i wypełnij "
            "formularz rezerwacji z danymi kontaktowymi."
        ),
    },
    {
        "question": "Czy potrzebuję konta, żeby zarezerwować?",
        "answer": "Nie — wystarczy formularz z e-mailem lub telefonem.",
    },
    {
        "question": "Jak działa kaucja?",
        "answer": (
            "Kaucja jest blokowana przy wydaniu auta i zwracana po zwrocie "
            "pojazdu zgodnie z regulaminem."
        ),
    },
    {
        "question": "Czy mogę anulować rezerwację?",
        "answer": "Zasady anulowania opisuje regulamin wynajmu.",
    },
]


def build_faq_context() -> str:
    lines = ["FAQ wypożyczalni:"]
    for item in FAQ_ITEMS:
        lines.append(f"- P: {item['question']}")
        lines.append(f"  O: {item['answer']}")
    return "\n".join(lines)
