from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from apps.website.services.chat_tools import (
    ChatToolResult,
    execute_estimate_price,
    execute_get_faq_snippet,
    execute_get_my_reservation_status,
    execute_search_available_cars,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

_DATE_RE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})(?:[T\s](?P<hour>\d{2}):(?P<minute>\d{2}))?",
)

_AVAILABILITY_KEYWORDS = (
    "dostepn",
    "wolne",
    "wolny",
    "wolna",
    "auto",
    "samochod",
    "flota",
    "pojazd",
)

_PRICE_KEYWORDS = (
    "wycen",
    "koszt",
    "cena",
    "ile koszt",
    "orientacyj",
    " zaplac",
)

_RESERVATION_STATUS_KEYWORDS = (
    "status",
    "moja rezerw",
    "mojej rezerw",
    "rezerwacja #",
)

_FAQ_KEYWORDS = (
    "regulamin",
    "faq",
    "anulow",
    "kaucj",
    "dokument",
)


def parse_datetime_match(match: re.Match[str]) -> datetime:
    hour = int(match.group("hour") or 10)
    minute = int(match.group("minute") or 0)
    date_part = match.group("date")
    return datetime.strptime(
        f"{date_part} {hour:02d}:{minute:02d}",
        "%Y-%m-%d %H:%M",
    ).replace(tzinfo=UTC)


def parse_date_range(text: str) -> tuple[datetime, datetime] | None:
    matches = list(_DATE_RE.finditer(text))
    if len(matches) < 2:
        return None
    start_at = parse_datetime_match(matches[0])
    end_at = parse_datetime_match(matches[1])
    if end_at <= start_at:
        return None
    return start_at, end_at


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _extract_car_id(text: str) -> int | None:
    match = re.search(r"(?:auto|car|id)\s*[#:]?\s*(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


class ChatToolRouter:
    """Heurystyczny router tooli dla providera mock (Sprint 8b Faza B)."""

    @staticmethod
    def run_for_message(
        text: str,
        *,
        user: AbstractBaseUser | None = None,
    ) -> tuple[ChatToolResult, ...]:
        lowered = text.lower()
        results: list[ChatToolResult] = []

        if _contains_any(lowered, _RESERVATION_STATUS_KEYWORDS):
            results.append(execute_get_my_reservation_status(user=user))

        if _contains_any(lowered, _FAQ_KEYWORDS) and not _contains_any(
            lowered,
            _AVAILABILITY_KEYWORDS + _PRICE_KEYWORDS,
        ):
            topic = _faq_topic_from_text(lowered)
            results.append(execute_get_faq_snippet(topic=topic))

        date_range = parse_date_range(text)
        if date_range is not None:
            start_at, end_at = date_range
            if _contains_any(lowered, _PRICE_KEYWORDS):
                car_id = _extract_car_id(text)
                if car_id is not None:
                    results.append(
                        execute_estimate_price(
                            car_id=car_id,
                            start_at=start_at,
                            end_at=end_at,
                        ),
                    )
                else:
                    search = execute_search_available_cars(
                        start_at=start_at,
                        end_at=end_at,
                    )
                    results.append(search)
                    first_car = (
                        search.data.get("cars", [{}])[0]
                        if search.data.get(
                            "cars",
                        )
                        else None
                    )
                    if first_car:
                        results.append(
                            execute_estimate_price(
                                car_id=first_car["id"],
                                start_at=start_at,
                                end_at=end_at,
                            ),
                        )
            elif _contains_any(lowered, _AVAILABILITY_KEYWORDS):
                results.append(
                    execute_search_available_cars(start_at=start_at, end_at=end_at),
                )

        return tuple(results)


def _faq_topic_from_text(text: str) -> str:
    for keyword in ("kaucj", "anul", "rezerw", "kont", "dokument"):
        if keyword in text:
            return keyword
    return ""
