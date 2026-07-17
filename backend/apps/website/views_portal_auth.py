from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.website.forms_portal_auth import PortalLoginRequestForm, PortalLoginVerifyForm
from apps.website.services.portal_auth import (
    SESSION_CHALLENGE_KEY,
    PortalLoginService,
)


def _client_ip(request: HttpRequest) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


@require_http_methods(["GET", "POST"])
def portal_login_request(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("customer_portal:home")

    form = PortalLoginRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            _customer, challenge = PortalLoginService.request_code(
                identifier=form.cleaned_data["identifier"],
                client_ip=_client_ip(request),
            )
        except ValidationError as exc:
            form.add_error(None, exc.messages[0] if exc.messages else str(exc))
        else:
            request.session[SESSION_CHALLENGE_KEY] = challenge
            messages.success(
                request,
                "Wyslalismy kod logowania na email powiazany z kontem.",
            )
            return redirect("customer_portal:otp_verify")

    return render(
        request,
        "website/portal/login_request.html",
        {"form": form},
    )


@require_http_methods(["GET", "POST"])
def portal_login_verify(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("customer_portal:home")

    challenge = request.session.get(SESSION_CHALLENGE_KEY)
    if not challenge:
        messages.error(request, "Najpierw popros o kod logowania.")
        return redirect("customer_portal:otp_request")

    form = PortalLoginVerifyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = PortalLoginService.verify_code(
                challenge=challenge,
                code=form.cleaned_data["code"],
            )
        except ValidationError as exc:
            form.add_error(None, exc.messages[0] if exc.messages else str(exc))
        else:
            request.session.pop(SESSION_CHALLENGE_KEY, None)
            login(request, user)
            next_url = request.GET.get("next") or reverse("customer_portal:home")
            return redirect(next_url)

    return render(
        request,
        "website/portal/login_verify.html",
        {"form": form},
    )
