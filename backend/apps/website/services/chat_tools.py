from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from django.urls import reverse

from apps.bookings.models import Reservation
from apps.bookings.selectors.customer import get_customer_by_user_id
from apps.bookings.selectors.reservation import list_reservations
from apps.fleet.models import Car, CarCategory
from apps.fleet.selectors.car import list_categories
from apps.website.faq_content import FAQ_ITEMS
from apps.website.selectors.availability_search import search_available_cars
from apps.website.selectors.price_quote import get_price_quote

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

PRICE_DISCLAIMER = (
    "Orientacyjna wycena — wiazaca kwota powstaje dopiero po rezerwacji "
    "ze snapshotem ceny."
)


@dataclass(frozen=True, slots=True)
class ChatToolResult:
    tool_name: str
    data: dict


def build_booking_deep_link(
    *,
    car_id: int,
    start_at: datetime,
    end_at: datetime,
) -> str:
    path = reverse("website:car_offer")
    params = urlencode(
        {
            "krok": "rezerwacja",
            "car": car_id,
            "start_at": start_at.strftime("%Y-%m-%dT%H:%M"),
            "end_at": end_at.strftime("%Y-%m-%dT%H:%M"),
        },
    )
    return f"{path}?{params}"


def execute_search_available_cars(
    *,
    start_at: datetime,
    end_at: datetime,
    category_id: int | None = None,
) -> ChatToolResult:
    result = search_available_cars(start_at, end_at, category_id=category_id)
    cars = []
    for car in result.cars[:10]:
        cars.append(
            {
                "id": car.pk,
                "label": f"{car.make} {car.model}",
                "registration_number": car.registration_number,
                "category": car.category.name,
                "booking_link": build_booking_deep_link(
                    car_id=car.pk,
                    start_at=start_at,
                    end_at=end_at,
                ),
            },
        )
    return ChatToolResult(
        tool_name="search_available_cars",
        data={
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "count": len(result.cars),
            "cars": cars,
        },
    )


def execute_estimate_price(
    *,
    car_id: int,
    start_at: datetime,
    end_at: datetime,
) -> ChatToolResult:
    car = Car.objects.select_related("category").filter(pk=car_id).first()
    if car is None:
        return ChatToolResult(
            tool_name="estimate_price",
            data={"error": f"Nie znaleziono auta o id {car_id}."},
        )
    quote = get_price_quote(car=car, start_at=start_at, end_at=end_at)
    return ChatToolResult(
        tool_name="estimate_price",
        data={
            "car_id": car.pk,
            "car_label": f"{car.make} {car.model} ({car.registration_number})",
            "total": str(quote.pricing.total),
            "currency": quote.pricing.currency,
            "booking_link": build_booking_deep_link(
                car_id=car.pk,
                start_at=start_at,
                end_at=end_at,
            ),
            "disclaimer": PRICE_DISCLAIMER,
        },
    )


def execute_get_faq_snippet(*, topic: str = "") -> ChatToolResult:
    needle = topic.strip().lower()
    items = FAQ_ITEMS
    if needle:
        items = [
            item
            for item in FAQ_ITEMS
            if needle in item["question"].lower() or needle in item["answer"].lower()
        ]
    snippets = [{"question": i["question"], "answer": i["answer"]} for i in items[:3]]
    return ChatToolResult(
        tool_name="get_faq_snippet",
        data={"topic": topic, "snippets": snippets},
    )


def execute_ask_clarifying_question(*, question: str) -> ChatToolResult:
    return ChatToolResult(
        tool_name="ask_clarifying_question",
        data={"question": question},
    )


def execute_get_deposit_info(*, category_id: int | None = None) -> ChatToolResult:
    categories = list(list_categories())
    if category_id is not None:
        categories = [c for c in categories if c.pk == category_id]
        if not categories:
            category = CarCategory.objects.filter(pk=category_id).first()
            if category is None:
                return ChatToolResult(
                    tool_name="get_deposit_info",
                    data={"error": "Nie znaleziono takiej kategorii."},
                )
            categories = [category]
    rows = [
        {
            "id": category.pk,
            "name": category.name,
            "deposit": str(category.deposit),
        }
        for category in categories
    ]
    return ChatToolResult(
        tool_name="get_deposit_info",
        data={"categories": rows},
    )


def execute_get_my_reservation_status(
    *,
    user: AbstractBaseUser | None,
) -> ChatToolResult:
    if user is None or not user.is_authenticated:
        return ChatToolResult(
            tool_name="get_my_reservation_status",
            data={"error": "Zaloguj się jako klient, aby sprawdzić status rezerwacji."},
        )
    customer = get_customer_by_user_id(user.pk)
    if customer is None:
        return ChatToolResult(
            tool_name="get_my_reservation_status",
            data={"error": "Brak profilu klienta powiązanego z kontem."},
        )
    reservations = list(
        list_reservations(customer_id=customer.pk).order_by("-start_at")[:5],
    )
    rows = [_reservation_summary(row) for row in reservations]
    return ChatToolResult(
        tool_name="get_my_reservation_status",
        data={"reservations": rows},
    )


def _reservation_summary(reservation: Reservation) -> dict:
    return {
        "id": reservation.pk,
        "status": reservation.get_status_display(),
        "status_code": reservation.status,
        "car": (
            f"{reservation.car.make} {reservation.car.model}"
            if reservation.car_id
            else ""
        ),
        "start_at": reservation.start_at.astimezone(UTC).isoformat(),
        "end_at": reservation.end_at.astimezone(UTC).isoformat(),
    }


def format_tool_results(results: tuple[ChatToolResult, ...]) -> str:
    if not results:
        return ""
    parts: list[str] = []
    for result in results:
        formatter = _FORMATTERS.get(result.tool_name)
        if formatter is not None:
            parts.append(formatter(result.data))
    return "\n\n".join(parts)


def _polish_available_cars_phrase(count: int) -> str:
    if count == 1:
        return "1 wolne auto"
    if 12 <= (count % 100) <= 14:
        return f"{count} wolnych aut"
    if (count % 10) in (2, 3, 4):
        return f"{count} wolne auta"
    return f"{count} wolnych aut"


def _format_chat_date(iso_value: str) -> str:
    """YYYY-MM-DD… → DD.MM.YYYY (opcjonalnie + HH:MM)."""
    date_part = iso_value[:10]
    try:
        year, month, day = date_part.split("-")
        label = f"{day}.{month}.{year}"
    except ValueError:
        return date_part
    if len(iso_value) >= 16 and iso_value[10] in "T ":
        time_part = iso_value[11:16]
        if time_part and time_part != "00:00":
            return f"{label}, {time_part}"
    return label


def _format_search(data: dict) -> str:
    if data.get("count", 0) == 0:
        return (
            "Na podany termin nie mam wolnych aut. Spróbuj inny termin "
            "albo skorzystaj z wyszukiwarki dostępności na stronie."
        )
    start_label = _format_chat_date(str(data["start_at"]))
    end_label = _format_chat_date(str(data["end_at"]))
    lines = [
        f"Na termin {start_label} — {end_label} mam "
        f"{_polish_available_cars_phrase(int(data['count']))}:",
    ]
    for car in data["cars"]:
        lines.append(
            f"- {car['label']} ({car['category']}) — zarezerwuj: {car['booking_link']}",
        )
    if data["count"] > len(data["cars"]):
        lines.append("… i więcej — pełna lista na stronie oferty.")
    lines.append(
        "Rezerwacji i płatności nie finalizuję w czacie — użyj linku albo "
        "formularza online."
    )
    return "\n".join(lines)


def _format_estimate(data: dict) -> str:
    if "error" in data:
        return str(data["error"])
    return (
        f"Orientacyjna wycena {data['car_label']}: "
        f"{data['total']} {data['currency']}. "
        f"{data['disclaimer']} "
        f"Rezerwacja: {data['booking_link']}"
    )


def _format_faq(data: dict) -> str:
    snippets = data.get("snippets") or []
    if not snippets:
        return (
            "Nie znalazłem pasującego fragmentu FAQ. "
            "Zobacz stronę FAQ albo zapytaj inaczej."
        )
    lines = ["Oto odpowiedzi z FAQ:"]
    for item in snippets:
        lines.append(f"**{item['question']}**")
        lines.append(item["answer"])
    return "\n".join(lines)


def _format_reservations(data: dict) -> str:
    if "error" in data:
        return str(data["error"])
    rows = data.get("reservations") or []
    if not rows:
        return "Nie masz jeszcze rezerwacji powiązanych z tym kontem."
    lines = ["Twoje ostatnie rezerwacje:"]
    for row in rows:
        lines.append(
            f"- #{row['id']}: {row['car']} — {row['status']} "
            f"({row['start_at'][:10]} → {row['end_at'][:10]})",
        )
    return "\n".join(lines)


def _format_clarifying(data: dict) -> str:
    return str(data.get("question") or "Możesz doprecyzować pytanie?")


def _format_deposit(data: dict) -> str:
    if "error" in data:
        return str(data["error"])
    rows = data.get("categories") or []
    if not rows:
        return "Nie mam jeszcze danych o kaucjach w cenniku kategorii."
    if len(rows) == 1:
        row = rows[0]
        return (
            f"Kaucja dla kategorii {row['name']}: {row['deposit']} PLN "
            "(zwrotna po rozliczeniu wynajmu)."
        )
    lines = ["Kaucje wg kategorii:"]
    for row in rows:
        lines.append(f"- {row['name']}: {row['deposit']} PLN")
    return "\n".join(lines)


_FORMATTERS = {
    "search_available_cars": _format_search,
    "estimate_price": _format_estimate,
    "get_faq_snippet": _format_faq,
    "get_my_reservation_status": _format_reservations,
    "ask_clarifying_question": _format_clarifying,
    "get_deposit_info": _format_deposit,
}
