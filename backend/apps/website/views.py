from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def landing(request: HttpRequest) -> HttpResponse:
    """Strona glowna kanalu publicznego (task 8.8)."""
    return render(request, "website/landing.html")
