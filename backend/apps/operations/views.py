from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.permissions import staff_required
from apps.bookings.selectors.rental import get_rental_by_id
from apps.documents.selectors.document import (
    get_handover_protocol_document,
    get_return_protocol_document,
)
from apps.operations.forms import HandoverProtocolForm, ReturnProtocolForm
from apps.operations.selectors.damage_comparison import get_return_damage_comparison
from apps.operations.selectors.protocol import (
    get_handover_for_rental,
    get_return_for_rental,
    list_rentals_pending_handover,
    list_rentals_pending_return,
)
from apps.operations.services.handover import HandoverService
from apps.operations.services.return_workflow import ReturnService
from apps.operations.services.surcharge_preview import SurchargePreviewService


def _parse_new_damage(cleaned_data: dict) -> list[dict]:
    desc = cleaned_data.get("new_damage_description", "").strip()
    if not desc:
        return []
    severity = cleaned_data.get("new_damage_severity") or "minor"
    return [
        {
            "description": desc,
            "location": cleaned_data.get("new_damage_location", "").strip(),
            "severity": severity,
        }
    ]


def _add_validation_errors_to_form(form, exc: ValidationError) -> None:
    if hasattr(exc, "message_dict"):
        for field, errs in exc.message_dict.items():
            for err in errs:
                form.add_error(field if field != "__all__" else None, err)
    elif exc.messages:
        form.add_error(None, exc.messages[0])
    else:
        form.add_error(None, str(exc))


@staff_required
def operations_home(request: HttpRequest) -> HttpResponse:
    pending_handover = list_rentals_pending_handover()
    pending_return = list_rentals_pending_return()
    return render(
        request,
        "operations/home.html",
        {
            "handover_count": pending_handover.count(),
            "return_count": pending_return.count(),
        },
    )


@staff_required
def handover_queue(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "operations/handover_queue.html",
        {"pending_handover": list_rentals_pending_handover()},
    )


@staff_required
def return_queue(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "operations/return_queue.html",
        {"pending_return": list_rentals_pending_return()},
    )


@staff_required
def handover_create(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    if rental is None:
        messages.error(request, "Nie znaleziono wynajmu.")
        return redirect("operations:handover_queue")

    existing = get_handover_for_rental(rental_id)
    if existing and existing.is_completed:
        return redirect("operations:handover_detail", rental_id=rental_id)

    car = rental.reservation.car
    initial = {"mileage": car.mileage, "fuel_level_percent": 100}
    if existing:
        initial = {
            "mileage": existing.mileage,
            "fuel_level_percent": existing.fuel_level_percent,
            "notes": existing.notes,
        }

    form = HandoverProtocolForm(
        request.POST or None, request.FILES or None, initial=initial
    )
    if request.method == "POST" and form.is_valid():
        new_damages = _parse_new_damage(form.cleaned_data)
        photos = request.FILES.getlist("photos")
        try:
            HandoverService.complete_handover(
                rental_id,
                mileage=form.cleaned_data["mileage"],
                fuel_level_percent=form.cleaned_data["fuel_level_percent"],
                signer_name=form.cleaned_data["signer_name"],
                signature_image=form.cleaned_data["signature_image"],
                notes=form.cleaned_data.get("notes", ""),
                photo_files=photos,
                new_damages=new_damages,
                performed_by_id=request.user.pk,
            )
        except ValidationError as exc:
            _add_validation_errors_to_form(form, exc)
        else:
            messages.success(request, "Zakończono protokół wydania. Wynajem aktywny.")
            return redirect("operations:handover_detail", rental_id=rental_id)

    from apps.fleet.models import Damage, DamageStatus

    active_damages = Damage.objects.filter(
        car=car,
        status=DamageStatus.ACTIVE,
    )
    return render(
        request,
        "operations/handover_form.html",
        {
            "rental": rental,
            "form": form,
            "active_damages": active_damages,
            "car_mileage": car.mileage,
        },
    )


@staff_required
def handover_detail(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    handover = get_handover_for_rental(rental_id)
    if rental is None or handover is None:
        messages.error(request, "Brak protokołu wydania.")
        return redirect("operations:handover_queue")
    return render(
        request,
        "operations/handover_detail.html",
        {
            "rental": rental,
            "handover": handover,
            "document": get_handover_protocol_document(handover.pk),
        },
    )


@staff_required
def return_create(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    if rental is None:
        messages.error(request, "Nie znaleziono wynajmu.")
        return redirect("operations:return_queue")

    handover = get_handover_for_rental(rental_id)
    if handover is None or not handover.is_completed:
        messages.warning(request, "Najpierw zakończ protokół wydania.")
        return redirect("operations:handover_create", rental_id=rental_id)

    existing = get_return_for_rental(rental_id)
    if existing and existing.is_completed:
        return redirect("operations:return_detail", rental_id=rental_id)

    initial = {
        "mileage": handover.mileage,
        "fuel_level_percent": handover.fuel_level_percent,
    }
    form = ReturnProtocolForm(
        request.POST or None, request.FILES or None, initial=initial
    )
    if request.method == "POST" and form.is_valid():
        photos = request.FILES.getlist("photos")
        try:
            ReturnService.complete_return(
                rental_id,
                mileage=form.cleaned_data["mileage"],
                fuel_level_percent=form.cleaned_data["fuel_level_percent"],
                signer_name=form.cleaned_data["signer_name"],
                signature_image=form.cleaned_data["signature_image"],
                notes=form.cleaned_data.get("notes", ""),
                surcharge_notes=form.cleaned_data.get("surcharge_notes", ""),
                photo_files=photos,
                new_damages=_parse_new_damage(form.cleaned_data),
                performed_by_id=request.user.pk,
            )
        except ValidationError as exc:
            _add_validation_errors_to_form(form, exc)
        else:
            messages.success(request, "Zakończono protokół zwrotu.")
            return redirect("operations:return_detail", rental_id=rental_id)

    from apps.fleet.models import Damage, DamageStatus

    car = rental.reservation.car
    active_damages = Damage.objects.filter(car=car, status=DamageStatus.ACTIVE)
    damage_comparison = (
        get_return_damage_comparison(handover) if handover.is_completed else []
    )
    initial_preview = SurchargePreviewService.preview(
        handover_mileage=handover.mileage,
        handover_fuel=handover.fuel_level_percent,
        return_mileage=initial["mileage"],
        return_fuel=initial["fuel_level_percent"],
    )
    return render(
        request,
        "operations/return_form.html",
        {
            "rental": rental,
            "handover": handover,
            "form": form,
            "active_damages": active_damages,
            "damage_comparison": damage_comparison,
            "surcharge_preview": initial_preview,
        },
    )


@staff_required
def return_surcharge_preview(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    handover = get_handover_for_rental(rental_id)
    if rental is None or handover is None or not handover.is_completed:
        return HttpResponse(status=404)

    try:
        mileage = int(request.GET.get("mileage", handover.mileage))
        fuel = int(request.GET.get("fuel_level_percent", handover.fuel_level_percent))
    except (TypeError, ValueError):
        return HttpResponse(status=400)

    preview = SurchargePreviewService.preview(
        handover_mileage=handover.mileage,
        handover_fuel=handover.fuel_level_percent,
        return_mileage=mileage,
        return_fuel=fuel,
    )
    return render(
        request,
        "operations/_surcharge_preview.html",
        {"preview": preview},
    )


@staff_required
def return_detail(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    return_protocol = get_return_for_rental(rental_id)
    if rental is None or return_protocol is None:
        messages.error(request, "Brak protokołu zwrotu.")
        return redirect("operations:return_queue")
    return render(
        request,
        "operations/return_detail.html",
        {
            "rental": rental,
            "return_protocol": return_protocol,
            "handover": return_protocol.handover,
            "document": get_return_protocol_document(return_protocol.pk),
        },
    )
