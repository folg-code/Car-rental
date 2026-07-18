from __future__ import annotations

from decimal import Decimal, InvalidOperation

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
from apps.fleet.fuel import percent_to_liters
from apps.fleet.models import DamageType
from apps.operations.forms import (
    CleanlinessStepForm,
    DriverStepForm,
    InteriorStepForm,
    OdometerStepForm,
    SignatureStepForm,
)
from apps.operations.models import (
    HANDOVER_STEPS,
    RETURN_REQUIRED_PHOTO_CATEGORIES,
    RETURN_STEPS,
    ProtocolDriver,
    ProtocolPhotoCategory,
    SignatureOutcome,
)
from apps.operations.selectors.damage_comparison import get_return_damage_comparison
from apps.operations.selectors.protocol import (
    get_handover_for_rental,
    get_return_for_rental,
    list_rentals_pending_handover,
    list_rentals_pending_return,
)
from apps.operations.services.handover import HandoverService
from apps.operations.services.return_workflow import ReturnService
from apps.operations.services.signature_upload import signature_file_from_form
from apps.operations.services.surcharge_preview import SurchargePreviewService


def _add_validation_errors(request: HttpRequest, exc: ValidationError) -> None:
    if hasattr(exc, "messages") and exc.messages:
        for msg in exc.messages:
            messages.error(request, msg)
    else:
        messages.error(request, str(exc))


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
    search = request.GET.get("q", "")
    return render(
        request,
        "operations/handover_queue.html",
        {
            "pending_handover": list_rentals_pending_handover(search=search),
            "search": search,
        },
    )


@staff_required
def return_queue(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("q", "")
    return render(
        request,
        "operations/return_queue.html",
        {
            "pending_return": list_rentals_pending_return(search=search),
            "search": search,
        },
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

    try:
        handover = HandoverService.start_handover(rental_id)
    except ValidationError as exc:
        _add_validation_errors(request, exc)
        return redirect("operations:handover_queue")

    step = request.GET.get("step") or handover.current_step or "driver"
    if step not in HANDOVER_STEPS:
        step = "driver"

    if request.method == "POST":
        action = request.POST.get("action", "save")
        try:
            if action == "save_driver":
                form = DriverStepForm(request.POST)
                if form.is_valid():
                    HandoverService.save_driver(handover, data=form.cleaned_data)
                    return redirect(f"{request.path}?step=odometer")
            elif action == "save_odometer":
                form = OdometerStepForm(request.POST, request.FILES)
                if form.is_valid():
                    HandoverService.save_odometer(
                        handover,
                        mileage=form.cleaned_data["mileage"],
                        fuel_level_percent=form.cleaned_data["fuel_level_percent"],
                        notes=form.cleaned_data.get("notes", ""),
                    )
                    if form.cleaned_data.get("odometer_photo"):
                        HandoverService.add_photo(
                            handover,
                            image=form.cleaned_data["odometer_photo"],
                            category=ProtocolPhotoCategory.ODOMETER,
                        )
                    if form.cleaned_data.get("fuel_photo"):
                        HandoverService.add_photo(
                            handover,
                            image=form.cleaned_data["fuel_photo"],
                            category=ProtocolPhotoCategory.FUEL_GAUGE,
                        )
                    return redirect(f"{request.path}?step=damages")
            elif action == "add_damage":
                HandoverService.add_damage_marker(
                    handover,
                    damage_type=request.POST.get("damage_type", "U"),
                    description=request.POST.get("description", ""),
                    pos_x=Decimal(request.POST.get("pos_x", "50")),
                    pos_y=Decimal(request.POST.get("pos_y", "50")),
                    size_note=request.POST.get("size_note", ""),
                    photo=request.FILES.get("photo"),
                )
                messages.success(request, "Dodano uszkodzenie.")
                return redirect(f"{request.path}?step=damages")
            elif action == "resolve_damage":
                HandoverService.resolve_damage_marker(
                    handover,
                    int(request.POST.get("marker_id")),
                    resolution=request.POST.get("resolution", "mistaken"),
                )
                return redirect(f"{request.path}?step=damages")
            elif action == "next_damages":
                handover.current_step = "photos"
                handover.save(update_fields=["current_step", "updated_at"])
                return redirect(f"{request.path}?step=photos")
            elif action == "add_photo":
                image = request.FILES.get("photo")
                if image:
                    HandoverService.add_photo(
                        handover,
                        image=image,
                        category=request.POST.get(
                            "category", ProtocolPhotoCategory.OTHER
                        ),
                        caption=request.POST.get("caption", ""),
                    )
                return redirect(f"{request.path}?step=photos")
            elif action == "next_photos":
                handover.current_step = "interior"
                handover.save(update_fields=["current_step", "updated_at"])
                return redirect(f"{request.path}?step=interior")
            elif action == "save_interior":
                form = InteriorStepForm(request.POST)
                if form.is_valid():
                    HandoverService.save_interior(
                        handover,
                        interior_notes={
                            "ok": form.cleaned_data.get("interior_ok"),
                            "issues": form.cleaned_data.get("interior_issues", []),
                            "description": form.cleaned_data.get(
                                "interior_description", ""
                            ),
                        },
                        inspection_notes={
                            "ok": form.cleaned_data.get("inspection_ok"),
                            "issues": form.cleaned_data.get("inspection_issues", []),
                            "description": form.cleaned_data.get(
                                "inspection_description", ""
                            ),
                        },
                    )
                    return redirect(f"{request.path}?step=equipment")
            elif action == "save_equipment":
                confirm_all = request.POST.get("confirm_all") == "1"
                lines = []
                for line in handover.equipment_lines.all():
                    lines.append(
                        {
                            "id": line.pk,
                            "status": request.POST.get(
                                f"status_{line.pk}", line.status
                            ),
                            "quantity_actual": request.POST.get(
                                f"qty_{line.pk}", line.quantity_expected
                            ),
                            "notes": request.POST.get(f"notes_{line.pk}", ""),
                        }
                    )
                HandoverService.save_equipment(
                    handover, lines=lines, confirm_all=confirm_all
                )
                return redirect(f"{request.path}?step=summary")
            elif action == "to_signature":
                handover.current_step = "signature"
                handover.save(update_fields=["current_step", "updated_at"])
                return redirect(f"{request.path}?step=signature")
            elif action == "finalize":
                form = SignatureStepForm(request.POST, request.FILES)
                if form.is_valid():
                    signature_image = signature_file_from_form(
                        uploaded=form.cleaned_data.get("signature_image"),
                        data_url=form.cleaned_data.get("signature_data_url"),
                    )
                    HandoverService.finalize_handover(
                        handover,
                        signer_name=form.cleaned_data.get("signer_name", ""),
                        signature_image=signature_image,
                        customer_notes=form.cleaned_data.get("customer_notes", ""),
                        performed_by_id=request.user.pk,
                    )
                    messages.success(
                        request, "Zakończono protokół wydania. Wynajem aktywny."
                    )
                    return redirect("operations:handover_detail", rental_id=rental_id)
        except (ValidationError, InvalidOperation, ValueError) as exc:
            if isinstance(exc, ValidationError):
                _add_validation_errors(request, exc)
            else:
                messages.error(request, str(exc))

    handover.refresh_from_db()
    try:
        driver = handover.driver
    except ProtocolDriver.DoesNotExist:
        driver = None
    car = rental.reservation.car
    reservation = rental.reservation
    step_index = HANDOVER_STEPS.index(step) if step in HANDOVER_STEPS else 1
    return render(
        request,
        "operations/handover_form.html",
        {
            "rental": rental,
            "reservation": reservation,
            "handover": handover,
            "driver": driver,
            "car": car,
            "step": step,
            "step_index": step_index,
            "steps": HANDOVER_STEPS,
            "fuel_tank_capacity_liters": car.fuel_tank_capacity_liters,
            "fuel_liters_preview": percent_to_liters(
                handover.fuel_level_percent or 100,
                car.fuel_tank_capacity_liters,
            ),
            "damage_types": DamageType.choices,
            "photo_categories": ProtocolPhotoCategory.choices,
            "driver_form": DriverStepForm(
                initial={
                    "first_name": getattr(driver, "first_name", ""),
                    "last_name": getattr(driver, "last_name", ""),
                    "email": getattr(driver, "email", ""),
                    "phone": getattr(driver, "phone", ""),
                    "address": getattr(driver, "address", ""),
                    "date_of_birth": getattr(driver, "date_of_birth", None),
                    "id_document_type": getattr(driver, "id_document_type", ""),
                    "id_document_number": getattr(driver, "id_document_number", ""),
                    "id_document_country": getattr(driver, "id_document_country", ""),
                    "license_number": getattr(driver, "license_number", ""),
                    "license_country": getattr(driver, "license_country", ""),
                    "license_issued_at": getattr(driver, "license_issued_at", None),
                    "license_expires_at": getattr(driver, "license_expires_at", None),
                    "document_verified": getattr(driver, "document_verified", False),
                    "license_valid": getattr(driver, "license_valid", False),
                    "license_category_ok": getattr(
                        driver, "license_category_ok", False
                    ),
                }
            )
            if step == "driver"
            else None,
            "odometer_form": OdometerStepForm(
                initial={
                    "mileage": handover.mileage or car.mileage,
                    "fuel_level_percent": handover.fuel_level_percent
                    if handover.fuel_level_percent is not None
                    else 100,
                    "notes": handover.notes,
                }
            )
            if step == "odometer"
            else None,
            "interior_form": InteriorStepForm() if step == "interior" else None,
            "signature_form": SignatureStepForm() if step == "signature" else None,
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

    try:
        return_protocol = ReturnService.start_return(rental_id)
    except ValidationError as exc:
        _add_validation_errors(request, exc)
        return redirect("operations:return_queue")

    step = request.GET.get("step") or return_protocol.current_step or "odometer"
    if step not in RETURN_STEPS:
        step = "odometer"

    if request.method == "POST":
        action = request.POST.get("action", "save")
        try:
            if action == "save_odometer":
                form = OdometerStepForm(request.POST, request.FILES)
                if form.is_valid():
                    ReturnService.save_odometer(
                        return_protocol,
                        mileage=form.cleaned_data["mileage"],
                        fuel_level_percent=form.cleaned_data["fuel_level_percent"],
                        actual_return_at=form.cleaned_data.get("actual_return_at"),
                        return_location=form.cleaned_data.get("return_location", ""),
                        organizational_notes=form.cleaned_data.get(
                            "organizational_notes", ""
                        ),
                    )
                    if form.cleaned_data.get("odometer_photo"):
                        ReturnService.add_photo(
                            return_protocol,
                            image=form.cleaned_data["odometer_photo"],
                            category=ProtocolPhotoCategory.ODOMETER,
                        )
                    if form.cleaned_data.get("fuel_photo"):
                        ReturnService.add_photo(
                            return_protocol,
                            image=form.cleaned_data["fuel_photo"],
                            category=ProtocolPhotoCategory.FUEL_GAUGE,
                        )
                    return redirect(f"{request.path}?step=damages")
            elif action == "add_damage":
                ReturnService.add_damage_marker(
                    return_protocol,
                    damage_type=request.POST.get("damage_type", "U"),
                    description=request.POST.get("description", ""),
                    pos_x=Decimal(request.POST.get("pos_x", "50")),
                    pos_y=Decimal(request.POST.get("pos_y", "50")),
                    size_note=request.POST.get("size_note", ""),
                    photo=request.FILES.get("photo"),
                )
                messages.success(request, "Dodano nowe uszkodzenie.")
                return redirect(f"{request.path}?step=damages")
            elif action == "next_damages":
                return_protocol.current_step = "photos"
                return_protocol.save(update_fields=["current_step", "updated_at"])
                return redirect(f"{request.path}?step=photos")
            elif action == "add_photo":
                image = request.FILES.get("photo")
                if image:
                    ReturnService.add_photo(
                        return_protocol,
                        image=image,
                        category=request.POST.get(
                            "category", ProtocolPhotoCategory.OTHER
                        ),
                        caption=request.POST.get("caption", ""),
                    )
                return redirect(f"{request.path}?step=photos")
            elif action == "next_photos":
                ReturnService.validate_required_photos(return_protocol)
                return_protocol.current_step = "equipment"
                return_protocol.save(update_fields=["current_step", "updated_at"])
                return redirect(f"{request.path}?step=equipment")
            elif action == "save_equipment":
                lines = []
                for line in return_protocol.equipment_lines.all():
                    lines.append(
                        {
                            "id": line.pk,
                            "status": request.POST.get(
                                f"status_{line.pk}", line.status
                            ),
                            "quantity_actual": request.POST.get(f"qty_{line.pk}"),
                            "notes": request.POST.get(f"notes_{line.pk}", ""),
                        }
                    )
                ReturnService.save_equipment(return_protocol, lines=lines)
                return redirect(f"{request.path}?step=cleanliness")
            elif action == "save_cleanliness":
                form = CleanlinessStepForm(request.POST, request.FILES)
                if form.is_valid():
                    data = {
                        "body": form.cleaned_data["body"],
                        "interior": form.cleaned_data["interior"],
                        "description": form.cleaned_data.get("description", ""),
                        "fee_suggestion": str(
                            form.cleaned_data.get("fee_suggestion") or ""
                        ),
                    }
                    if form.cleaned_data.get("photo"):
                        ReturnService.add_photo(
                            return_protocol,
                            image=form.cleaned_data["photo"],
                            category=ProtocolPhotoCategory.DETAIL,
                            caption="czystosc",
                        )
                        data["photo_attached"] = True
                    ReturnService.save_cleanliness(return_protocol, cleanliness=data)
                    return redirect(f"{request.path}?step=settlement")
            elif action == "save_settlement":
                decisions = []
                for line in return_protocol.settlement_lines.all():
                    decisions.append(
                        {
                            "id": line.pk,
                            "decision": request.POST.get(
                                f"decision_{line.pk}", line.decision
                            ),
                            "staff_note": request.POST.get(f"note_{line.pk}", ""),
                        }
                    )
                ReturnService.save_settlement_decisions(
                    return_protocol, decisions=decisions
                )
                return redirect(f"{request.path}?step=summary")
            elif action == "to_signature":
                return_protocol.current_step = "signature"
                return_protocol.save(update_fields=["current_step", "updated_at"])
                return redirect(f"{request.path}?step=signature")
            elif action == "finalize":
                form = SignatureStepForm(request.POST, request.FILES)
                if form.is_valid():
                    outcome = form.cleaned_data.get("outcome", SignatureOutcome.SIGNED)
                    signature_image = signature_file_from_form(
                        uploaded=form.cleaned_data.get("signature_image"),
                        data_url=form.cleaned_data.get("signature_data_url"),
                    )
                    ReturnService.finalize_return(
                        return_protocol,
                        signer_name=form.cleaned_data.get("signer_name", ""),
                        signature_image=signature_image,
                        customer_notes=form.cleaned_data.get("customer_notes", ""),
                        outcome=outcome,
                        closure_reason=form.cleaned_data.get("closure_reason", ""),
                        performed_by_id=request.user.pk,
                        require_photos=True,
                    )
                    messages.success(request, "Zakończono protokół zwrotu.")
                    return redirect("operations:return_detail", rental_id=rental_id)
        except (ValidationError, InvalidOperation, ValueError) as exc:
            if isinstance(exc, ValidationError):
                _add_validation_errors(request, exc)
            else:
                messages.error(request, str(exc))

    return_protocol.refresh_from_db()
    preview = None
    if return_protocol.mileage is not None and handover.mileage is not None:
        preview = SurchargePreviewService.preview(
            handover_mileage=handover.mileage,
            handover_fuel=handover.fuel_level_percent or 0,
            return_mileage=return_protocol.mileage,
            return_fuel=return_protocol.fuel_level_percent or 0,
            tank_capacity_liters=rental.reservation.car.fuel_tank_capacity_liters,
            handover_fuel_level=handover.fuel_level,
            return_fuel_level=return_protocol.fuel_level,
        )
    present_cats = set(return_protocol.photos.values_list("category", flat=True))
    step_index = RETURN_STEPS.index(step) if step in RETURN_STEPS else 1
    return render(
        request,
        "operations/return_form.html",
        {
            "rental": rental,
            "handover": handover,
            "return_protocol": return_protocol,
            "step": step,
            "step_index": step_index,
            "steps": RETURN_STEPS,
            "fuel_tank_capacity_liters": (
                rental.reservation.car.fuel_tank_capacity_liters
            ),
            "fuel_liters_preview": percent_to_liters(
                return_protocol.fuel_level_percent
                if return_protocol.fuel_level_percent is not None
                else (handover.fuel_level_percent or 100),
                rental.reservation.car.fuel_tank_capacity_liters,
            ),
            "damage_types": DamageType.choices,
            "photo_categories": ProtocolPhotoCategory.choices,
            "required_photos": RETURN_REQUIRED_PHOTO_CATEGORIES,
            "present_photo_categories": present_cats,
            "damage_comparison": get_return_damage_comparison(handover),
            "surcharge_preview": preview,
            "odometer_form": OdometerStepForm(
                initial={
                    "mileage": return_protocol.mileage or handover.mileage,
                    "fuel_level_percent": return_protocol.fuel_level_percent
                    if return_protocol.fuel_level_percent is not None
                    else (handover.fuel_level_percent or 100),
                    "return_location": return_protocol.return_location,
                    "organizational_notes": return_protocol.organizational_notes,
                }
            )
            if step == "odometer"
            else None,
            "cleanliness_form": CleanlinessStepForm(
                initial=return_protocol.cleanliness or {}
            )
            if step == "cleanliness"
            else None,
            "signature_form": SignatureStepForm() if step == "signature" else None,
        },
    )


@staff_required
def return_surcharge_preview(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    handover = get_handover_for_rental(rental_id)
    if rental is None or handover is None or not handover.is_completed:
        return HttpResponse(status=404)

    try:
        mileage = int(request.GET.get("mileage", handover.mileage or 0))
        fuel = int(
            request.GET.get("fuel_level_percent", handover.fuel_level_percent or 0)
        )
    except (TypeError, ValueError):
        return HttpResponse(status=400)

    preview = SurchargePreviewService.preview(
        handover_mileage=handover.mileage or 0,
        handover_fuel=handover.fuel_level_percent or 0,
        return_mileage=mileage,
        return_fuel=fuel,
        tank_capacity_liters=rental.reservation.car.fuel_tank_capacity_liters,
        handover_fuel_level=handover.fuel_level,
        return_fuel_level=request.GET.get("fuel_level", ""),
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
