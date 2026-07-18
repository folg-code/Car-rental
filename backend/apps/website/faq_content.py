"""Treści FAQ wykorzystywane w asystencie AI (Sprint 8b / mock)."""

from __future__ import annotations

FAQ_ITEMS: list[dict[str, str]] = [
    {
        "question": "Jak zarezerwować auto online?",
        "answer": (
            "Sprawdź dostępność aut, zobacz orientacyjną wycenę i wypełnij "
            "formularz rezerwacji z danymi kontaktowymi. Nie wymagamy konta."
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
            "pojazdu, jeśli nie ma uszkodzeń i dopłat — szczegóły w regulaminie."
        ),
    },
    {
        "question": "Czy mogę anulować rezerwację?",
        "answer": (
            "Zasady anulowania i ewentualne opłaty opisuje regulamin wynajmu. "
            "W razie wątpliwości skorzystaj ze strony Kontakt."
        ),
    },
    {
        "question": "Jakie dokumenty są potrzebne?",
        "answer": (
            "Do odbioru pojazdu potrzebujesz ważnego prawa jazdy kategorii B "
            "oraz dokumentu tożsamości. Szczegóły wieku kierowcy i kaucji "
            "znajdziesz w regulaminie."
        ),
    },
    {
        "question": "Jaki jest minimalny wiek kierowcy?",
        "answer": (
            "Standardowo wynajem jest dostępny dla osób pełnoletnich "
            "z ważnym prawem jazdy. Limity wieku i stażu mogą zależeć "
            "od kategorii auta — sprawdź regulamin."
        ),
    },
    {
        "question": "Jak oddać auto i jak tankować?",
        "answer": (
            "Pojazd oddajesz w umówionym terminie i miejscu zwrotu. "
            "Poziom paliwa powinien odpowiadać stanowi z protokołu wydania — "
            "niedobór może skutkować dopłatą."
        ),
    },
    {
        "question": "Jakie są godziny odbioru i zwrotu?",
        "answer": (
            "Termin odbioru i zwrotu wybierasz przy rezerwacji. "
            "Domyślnie asystent przyjmuje godzinę 10:00, jeśli nie podasz innej. "
            "Szczegóły godzin biura — strona Kontakt / FAQ."
        ),
    },
]


DEMO_CHAT_PROMPTS: list[dict[str, str]] = [
    {
        "label": "Wolne auta na jutro",
        "message": "Czy są wolne auta na jutro?",
    },
    {
        "label": "Kaucja za SUV",
        "message": "Ile kaucji za SUV?",
    },
    {
        "label": "Auto na weekend",
        "message": "Chcę zarezerwować auto na weekend",
    },
    {
        "label": "Dokumenty",
        "message": "Jakie dokumenty są potrzebne?",
    },
    {
        "label": "Jak działa kaucja?",
        "message": "Jak działa kaucja?",
    },
]


def build_faq_context() -> str:
    lines = ["FAQ wypożyczalni:"]
    for item in FAQ_ITEMS:
        lines.append(f"- P: {item['question']}")
        lines.append(f"  O: {item['answer']}")
    return "\n".join(lines)
