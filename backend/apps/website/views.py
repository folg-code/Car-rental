from __future__ import annotations

from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.payments.models import PaymentIntent
from apps.website.forms import AvailabilitySearchForm, PriceQuoteForm, PublicBookingForm
from apps.website.selectors.availability_search import search_available_cars
from apps.website.selectors.fleet_catalog import get_public_fleet_catalog
from apps.website.selectors.price_quote import get_price_quote
from apps.website.selectors.public_booking import (
    get_public_reservation_summary,
    reservation_display_total,
)
from apps.website.services.public_booking import PublicBookingOrchestrator
from apps.website.services.public_payment import PublicPaymentOrchestrator

PUBLIC_BOOKING_SESSION_KEY = "public_booking_id"


def landing(request: HttpRequest) -> HttpResponse:
    """Strona glowna kanalu publicznego (task 8.8)."""
    return render(request, "website/landing.html")


def fleet_list(request: HttpRequest) -> HttpResponse:
    """Publiczny katalog floty (task 8.9)."""
    catalog = get_public_fleet_catalog(
        category_slug=request.GET.get("kategoria"),
    )
    return render(
        request,
        "website/fleet_list.html",
        {
            "catalog": catalog,
            "categories": catalog.categories,
            "cars": catalog.cars,
            "selected_category_slug": catalog.selected_category_slug,
        },
    )


def availability_search(request: HttpRequest) -> HttpResponse:
    """Wyszukiwarka dostepnosci floty (task 8.10)."""
    form = AvailabilitySearchForm(request.POST or None)
    result = None
    if request.method == "POST" and form.is_valid():
        category = form.cleaned_data.get("category")
        result = search_available_cars(
            form.cleaned_data["start_at"],
            form.cleaned_data["end_at"],
            category_id=category.pk if category else None,
        )
    return render(
        request,
        "website/availability_search.html",
        {
            "form": form,
            "result": result,
            "searched": result is not None,
        },
    )


def price_quote(request: HttpRequest) -> HttpResponse:
    """Orientacyjna wycena wynajmu (task 8.11)."""
    data = request.POST if request.method == "POST" else request.GET
    form = PriceQuoteForm(data or None)
    result = None
    if data and form.is_valid():
        try:
            result = get_price_quote(
                car=form.cleaned_data["car"],
                start_at=form.cleaned_data["start_at"],
                end_at=form.cleaned_data["end_at"],
                extra_codes=form.cleaned_data.get("extras"),
            )
        except ValidationError as exc:
            message = exc.messages[0] if exc.messages else str(exc)
            form.add_error(None, message)
    return render(
        request,
        "website/price_quote.html",
        {
            "form": form,
            "result": result,
            "quoted": result is not None,
        },
    )


def public_booking(request: HttpRequest) -> HttpResponse:
    """Formularz rezerwacji online (task 8.12)."""
    if request.method == "POST":
        form = PublicBookingForm(request.POST)
        if form.is_valid():
            try:
                result = PublicBookingOrchestrator.submit(
                    car=form.cleaned_data["car"],
                    start_at=form.cleaned_data["start_at"],
                    end_at=form.cleaned_data["end_at"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    email=form.cleaned_data.get("email") or "",
                    phone=form.cleaned_data.get("phone") or "",
                    extra_codes=form.cleaned_data.get("extras"),
                    notes=form.cleaned_data.get("notes") or "",
                )
            except ValidationError as exc:
                message = exc.messages[0] if exc.messages else str(exc)
                form.add_error(None, message)
            else:
                request.session[PUBLIC_BOOKING_SESSION_KEY] = result.reservation.pk
                return HttpResponseRedirect(reverse("website:booking_confirmation"))
    else:
        form = PublicBookingForm(initial=_booking_form_initial(request))
    return render(
        request,
        "website/public_booking.html",
        {"form": form},
    )


def booking_confirmation(request: HttpRequest) -> HttpResponse:
    """Potwierdzenie rezerwacji online (task 8.12)."""
    reservation_id = request.session.pop(PUBLIC_BOOKING_SESSION_KEY, None)
    if reservation_id is None:
        return redirect("website:home")
    return _render_booking_confirmation(request, reservation_id)


def booking_confirmation_by_id(
    request: HttpRequest,
    reservation_id: int,
) -> HttpResponse:
    """Potwierdzenie rezerwacji po anulowaniu platnosci (task 9.5)."""
    return _render_booking_confirmation(request, reservation_id)


def _render_booking_confirmation(
    request: HttpRequest,
    reservation_id: int,
) -> HttpResponse:
    reservation = get_public_reservation_summary(reservation_id)
    if reservation is None:
        return redirect("website:home")
    return render(
        request,
        "website/booking_confirmation.html",
        {
            "reservation": reservation,
            "total": reservation_display_total(reservation),
        },
    )


def start_payment(request: HttpRequest, reservation_id: int) -> HttpResponse:
    """Inicjacja platnosci online — redirect do bramki (task 9.5)."""
    try:
        session = PublicPaymentOrchestrator.start_online_payment(
            reservation_id,
            success_url=request.build_absolute_uri(
                PublicPaymentOrchestrator.build_success_url(reservation_id),
            ),
            cancel_url=request.build_absolute_uri(
                PublicPaymentOrchestrator.build_cancel_url(reservation_id),
            ),
        )
    except ValidationError as exc:
        message = exc.messages[0] if exc.messages else str(exc)
        reservation = get_public_reservation_summary(reservation_id)
        if reservation is None:
            return redirect("website:home")
        return render(
            request,
            "website/booking_confirmation.html",
            {
                "reservation": reservation,
                "total": reservation_display_total(reservation),
                "payment_error": message,
            },
            status=400,
        )
    return HttpResponseRedirect(session.checkout_url)


def mock_payment_checkout(request: HttpRequest) -> HttpResponse:
    """Mock bramki — strona testowa platnosci (dev/test, task 9.5)."""
    external_reference = request.GET.get("ref", "")
    intent_id = request.GET.get("intent", "")
    intent = (
        PaymentIntent.objects.filter(
            pk=intent_id,
            external_reference=external_reference,
        ).first()
        if intent_id and external_reference
        else None
    )
    if intent is None:
        return redirect("website:home")

    if request.method == "POST":
        PublicPaymentOrchestrator.complete_mock_payment(
            external_reference=external_reference,
        )
        return redirect(
            "website:payment_success",
            reservation_id=intent.reservation_id,
        )

    return render(
        request,
        "website/mock_payment_checkout.html",
        {"intent": intent},
    )


def payment_success(request: HttpRequest, reservation_id: int) -> HttpResponse:
    """Strona sukcesu platnosci online (task 9.5)."""
    reservation = get_public_reservation_summary(reservation_id)
    if reservation is None:
        return redirect("website:home")
    return render(
        request,
        "website/payment_success.html",
        {
            "reservation": reservation,
            "total": reservation_display_total(reservation),
        },
    )


def _booking_form_initial(request: HttpRequest) -> dict[str, object]:
    initial: dict[str, object] = {}
    if car_id := request.GET.get("car"):
        try:
            initial["car"] = int(car_id)
        except ValueError:
            pass
    for field in ("start_at", "end_at"):
        if raw := request.GET.get(field):
            initial[field] = raw
    return initial


def terms(request: HttpRequest) -> HttpResponse:
    """Regulamin — placeholder (task 8.13)."""
    return render(request, "website/terms.html")


def contact(request: HttpRequest) -> HttpResponse:
    """Kontakt — placeholder (task 8.13)."""
    return render(request, "website/contact.html")


def faq(request: HttpRequest) -> HttpResponse:
    """FAQ — przykladowe pytania, bez tresci produkcyjnej (task 8.13)."""
    return render(request, "website/faq.html")
