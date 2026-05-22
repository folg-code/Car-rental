from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import staff_required
from apps.fleet.forms import (
    AvailabilityBlockForm,
    CarCategoryForm,
    CarForm,
    DamageForm,
)
from apps.fleet.models import AvailabilityBlock, Car, CarCategory
from apps.fleet.selectors.car import get_car_detail, list_cars, list_categories
from apps.fleet.services.damage import DamageService
from apps.fleet.services.maintenance import FleetMaintenanceService


@staff_required
def car_list(request: HttpRequest) -> HttpResponse:
    status_filter = request.GET.get("status", "")
    cars = list_cars(status=status_filter or None)
    return render(
        request,
        "fleet/car_list.html",
        {
            "cars": cars,
            "status_filter": status_filter,
            "categories": list_categories(),
        },
    )


@staff_required
def car_detail(request: HttpRequest, pk: int) -> HttpResponse:
    car = get_car_detail(pk)
    if car is None:
        messages.error(request, "Nie znaleziono pojazdu.")
        return redirect("fleet:car_list")
    return render(request, "fleet/car_detail.html", {"car": car})


@staff_required
def car_create(request: HttpRequest) -> HttpResponse:
    form = CarForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        car = form.save()
        messages.success(request, f"Dodano pojazd {car.registration_number}.")
        return redirect("fleet:car_detail", pk=car.pk)
    return render(
        request,
        "fleet/car_form.html",
        {"form": form, "title": "Nowy pojazd"},
    )


@staff_required
def car_edit(request: HttpRequest, pk: int) -> HttpResponse:
    car = get_object_or_404(Car, pk=pk)
    form = CarForm(request.POST or None, instance=car)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Zapisano zmiany pojazdu.")
        return redirect("fleet:car_detail", pk=car.pk)
    return render(
        request,
        "fleet/car_form.html",
        {"form": form, "title": f"Edycja — {car.registration_number}", "car": car},
    )


@staff_required
def category_list(request: HttpRequest) -> HttpResponse:
    form = CarCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Dodano kategorie.")
        return redirect("fleet:category_list")
    return render(
        request,
        "fleet/category_list.html",
        {"categories": list_categories(), "form": form},
    )


@staff_required
def category_edit(request: HttpRequest, pk: int) -> HttpResponse:
    category = get_object_or_404(CarCategory, pk=pk)
    form = CarCategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Zapisano kategorie {category.name}.")
        return redirect("fleet:category_list")
    return render(
        request,
        "fleet/category_form.html",
        {"form": form, "title": f"Edycja — {category.name}", "category": category},
    )


@staff_required
def block_create(request: HttpRequest, car_pk: int) -> HttpResponse:
    car = get_object_or_404(Car, pk=car_pk)
    form = AvailabilityBlockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            FleetMaintenanceService.create_availability_block(
                car_id=car.pk,
                start_at=form.cleaned_data["start_at"],
                end_at=form.cleaned_data["end_at"],
                reason=form.cleaned_data["reason"],
                block_type=form.cleaned_data["block_type"],
                created_by_id=request.user.pk,
            )
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, errs in exc.message_dict.items():
                    for err in errs:
                        form.add_error(field if field != "__all__" else None, err)
            else:
                form.add_error(None, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(request, "Dodano blokade dostepnosci.")
            return redirect("fleet:car_detail", pk=car.pk)
    return render(
        request,
        "fleet/block_form.html",
        {"form": form, "car": car},
    )


@staff_required
def block_delete(request: HttpRequest, car_pk: int, block_pk: int) -> HttpResponse:
    car = get_object_or_404(Car, pk=car_pk)
    block = get_object_or_404(AvailabilityBlock, pk=block_pk, car=car)
    if request.method == "POST":
        FleetMaintenanceService.delete_availability_block(block)
        messages.success(request, "Usunieto blokade.")
        return redirect("fleet:car_detail", pk=car.pk)
    return render(
        request,
        "fleet/block_confirm_delete.html",
        {"car": car, "block": block},
    )


@staff_required
def damage_create(request: HttpRequest, car_pk: int) -> HttpResponse:
    car = get_object_or_404(Car, pk=car_pk)
    form = DamageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        DamageService.report_damage(car=car, **form.cleaned_data)
        messages.success(request, "Zarejestrowano uszkodzenie.")
        return redirect("fleet:car_detail", pk=car.pk)
    return render(
        request,
        "fleet/damage_form.html",
        {"form": form, "car": car},
    )
