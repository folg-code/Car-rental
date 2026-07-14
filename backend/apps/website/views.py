from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.website.forms import AvailabilitySearchForm
from apps.website.selectors.availability_search import search_available_cars
from apps.website.selectors.fleet_catalog import get_public_fleet_catalog


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
