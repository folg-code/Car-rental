from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

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
