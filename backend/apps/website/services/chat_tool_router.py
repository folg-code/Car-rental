from __future__ import annotations

import re
import unicodedata
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from apps.fleet.selectors.car import list_categories
from apps.website.services.chat_tools import (
    ChatToolResult,
    execute_ask_clarifying_question,
    execute_estimate_price,
    execute_get_deposit_info,
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

_BOOKING_KEYWORDS = (
    "zarezerw",
    "rezerwacj",
    "wynajm",
    "wezme",
    "wezmę",
)

_PRICE_KEYWORDS = (
    "wycen",
    "koszt",
    "cena",
    "ile koszt",
    "orientacyj",
    " zaplac",
)

_DEPOSIT_KEYWORDS = (
    "kaucj",
    "depozyt",
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
    "dokument",
)

_WEEKDAY_ALIASES: dict[str, int] = {
    "poniedzialek": 0,
    "poniedzialku": 0,
    "wtorek": 1,
    "wtorku": 1,
    "sroda": 2,
    "srode": 2,
    "srody": 2,
    "czwartek": 3,
    "czwartku": 3,
    "piatek": 4,
    "piatku": 4,
    "sobota": 5,
    "sobote": 5,
    "soboty": 5,
    "niedziela": 6,
    "niedziele": 6,
    "niedzieli": 6,
}

_CATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "suv": ("suv",),
    "kompakt": ("kompakt", "male", "małe", "ekonom"),
    "premium": ("premium", "luksus"),
    "rodzinne": ("rodzin", "kombi", "van"),
}


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _chat_tz() -> ZoneInfo:
    try:
        return ZoneInfo(settings.TIME_ZONE)
    except Exception:
        return ZoneInfo("Europe/Warsaw")


def _default_hours() -> tuple[int, int]:
    pickup = int(getattr(settings, "CHAT_DEFAULT_PICKUP_HOUR", 10))
    ret = int(getattr(settings, "CHAT_DEFAULT_RETURN_HOUR", 10))
    return pickup, ret


def _at_local(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(
        day.year,
        day.month,
        day.day,
        hour,
        minute,
        tzinfo=_chat_tz(),
    )


def parse_datetime_match(match: re.Match[str]) -> datetime:
    pickup_hour, _ = _default_hours()
    hour = int(match.group("hour") or pickup_hour)
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


def parse_relative_date_range(
    text: str,
    *,
    today: date | None = None,
) -> tuple[datetime, datetime] | None:
    """Polish relative dates: jutro, pojutrze, weekend, od X do Y."""
    folded = _fold(text)
    today = today or timezone.localdate()
    pickup_h, return_h = _default_hours()

    weekday_range = _parse_weekday_range(folded, today=today)
    if weekday_range is not None:
        start_day, end_day = weekday_range
        start_at = _at_local(start_day, pickup_h)
        end_at = _at_local(end_day, return_h)
        if end_at <= start_at:
            end_at = _at_local(end_day + timedelta(days=1), return_h)
        return start_at, end_at

    if "weekend" in folded:
        days_until_sat = (5 - today.weekday()) % 7
        saturday = today + timedelta(days=days_until_sat)
        sunday = saturday + timedelta(days=1)
        return _at_local(saturday, pickup_h), _at_local(sunday, return_h)

    if "pojutrze" in folded:
        day = today + timedelta(days=2)
        return _at_local(day, pickup_h), _at_local(day + timedelta(days=1), return_h)

    if "jutro" in folded:
        day = today + timedelta(days=1)
        return _at_local(day, pickup_h), _at_local(day + timedelta(days=1), return_h)

    if "dzisiaj" in folded or "dzis" in folded:
        return _at_local(today, pickup_h), _at_local(
            today + timedelta(days=1),
            return_h,
        )

    return None


def _parse_weekday_range(
    folded: str,
    *,
    today: date,
) -> tuple[date, date] | None:
    match = re.search(
        r"od\s+(?P<start>\w+)\s+do\s+(?P<end>\w+)",
        folded,
    )
    if match is None:
        return None
    start_wd = _WEEKDAY_ALIASES.get(match.group("start"))
    end_wd = _WEEKDAY_ALIASES.get(match.group("end"))
    if start_wd is None or end_wd is None:
        return None
    start_day = today + timedelta(days=(start_wd - today.weekday()) % 7)
    end_day = today + timedelta(days=(end_wd - today.weekday()) % 7)
    if end_day < start_day:
        end_day += timedelta(days=7)
    return start_day, end_day


def resolve_date_range(text: str) -> tuple[datetime, datetime] | None:
    return parse_date_range(text) or parse_relative_date_range(text)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    folded = _fold(text)
    return any(_fold(keyword) in folded for keyword in keywords)


def _extract_car_id(text: str) -> int | None:
    match = re.search(r"(?:auto|car|id)\s*[#:]?\s*(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_category_id(text: str) -> int | None:
    folded = _fold(text)
    categories = list(list_categories())
    for category in categories:
        name = _fold(category.name)
        slug = _fold(category.slug.replace("-", " "))
        if name and name in folded:
            return category.pk
        if slug and slug in folded:
            return category.pk
    for category in categories:
        aliases = _CATEGORY_ALIASES.get(_fold(category.slug), ())
        if any(alias in folded for alias in aliases):
            return category.pk
        for alias_key, alias_words in _CATEGORY_ALIASES.items():
            if alias_key in _fold(category.name) or alias_key in _fold(category.slug):
                if any(word in folded for word in alias_words):
                    return category.pk
    for alias_key, alias_words in _CATEGORY_ALIASES.items():
        if any(word in folded for word in (alias_key, *alias_words)):
            for category in categories:
                if alias_key in _fold(category.name) or alias_key in _fold(
                    category.slug
                ):
                    return category.pk
    return None


class ChatToolRouter:
    """Heurystyczny router tooli dla providera mock (Sprint 8b + 12.1)."""

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

        if _contains_any(lowered, _DEPOSIT_KEYWORDS):
            results.append(
                execute_get_deposit_info(category_id=_extract_category_id(lowered)),
            )

        if _contains_any(lowered, _FAQ_KEYWORDS) and not _contains_any(
            lowered,
            _AVAILABILITY_KEYWORDS + _PRICE_KEYWORDS + _DEPOSIT_KEYWORDS,
        ):
            topic = _faq_topic_from_text(lowered)
            results.append(execute_get_faq_snippet(topic=topic))

        wants_availability = _contains_any(
            lowered,
            _AVAILABILITY_KEYWORDS + _BOOKING_KEYWORDS,
        )
        wants_price = _contains_any(lowered, _PRICE_KEYWORDS)
        date_range = resolve_date_range(text)
        category_id = _extract_category_id(lowered)

        if (wants_availability or wants_price) and date_range is None:
            if wants_availability or wants_price:
                results.append(
                    execute_ask_clarifying_question(
                        question="Na jaki termin mam sprawdzic dostepnosc?",
                    ),
                )
            return tuple(results)

        if date_range is not None:
            start_at, end_at = date_range
            if wants_price:
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
                        category_id=category_id,
                    )
                    results.append(search)
                    first_car = (
                        search.data.get("cars", [{}])[0]
                        if search.data.get("cars")
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
            elif wants_availability:
                results.append(
                    execute_search_available_cars(
                        start_at=start_at,
                        end_at=end_at,
                        category_id=category_id,
                    ),
                )

        return tuple(results)


def _faq_topic_from_text(text: str) -> str:
    for keyword in ("anul", "rezerw", "kont", "dokument", "regulamin"):
        if keyword in _fold(text):
            return keyword
    return ""
