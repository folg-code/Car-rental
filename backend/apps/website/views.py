from __future__ import annotations

from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.website.forms import AvailabilitySearchForm, PriceQuoteForm
from apps.website.selectors.availability_search import search_available_cars
from apps.website.selectors.fleet_catalog import get_public_fleet_catalog
from apps.website.selectors.price_quote import get_price_quote


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
