from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import staff_required
from apps.bookings.forms import CustomerForm, ReservationCancelForm, ReservationForm
from apps.bookings.models import (
    Customer,
    Rental,
    RentalStatus,
    Reservation,
    ReservationPricingMode,
    ReservationStatus,
)
from apps.bookings.selectors.customer import get_customer_by_id, list_customers
from apps.bookings.selectors.rental import get_rental_by_id, list_rentals
from apps.bookings.selectors.reservation import get_reservation_by_id, list_reservations
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.selectors.document import list_documents
from apps.payments.selectors.payment import get_rental_payment_summary
from apps.pricing.selectors.price_list import (
    get_price_list_for_date,
    list_active_extras,
)


def _add_validation_errors_to_form(form, exc: ValidationError) -> None:
    if hasattr(exc, "message_dict"):
        for field, errs in exc.message_dict.items():
            for err in errs:
                form.add_error(field if field != "__all__" else None, err)
    elif exc.messages:
        form.add_error(None, exc.messages[0])
    else:
        form.add_error(None, str(exc))


# --- Rezerwacje ---


@staff_required
def reservation_list(request: HttpRequest) -> HttpResponse:
    status_filter = request.GET.get("status", "").strip()
    reservations = list_reservations(
        status=status_filter or None,
    )
    return render(
        request,
        "bookings/reservation_list.html",
        {
            "reservations": reservations,
            "status_filter": status_filter,
            "status_choices": ReservationStatus.choices,
        },
    )


@staff_required
def reservation_detail(request: HttpRequest, pk: int) -> HttpResponse:
    reservation = get_reservation_by_id(pk)
    if reservation is None:
        messages.error(request, "Nie znaleziono rezerwacji.")
        return redirect("bookings:reservation_list")
    price_list = get_price_list_for_date(reservation.start_at.date())
    if reservation.pricing_mode == ReservationPricingMode.PRICE_LIST:
        price_list = reservation.price_list
    available_extras = (
        list_active_extras(price_list)
        if price_list is not None
        and reservation.pricing_mode != ReservationPricingMode.CUSTOM
        else []
    )
    return render(
        request,
        "bookings/reservation_detail.html",
        {
            "reservation": reservation,
            "price_total": PriceSnapshotService.reservation_total(reservation),
            "can_recalculate_price": (
                PriceSnapshotService.can_recalculate(reservation)
                and reservation.pricing_mode != ReservationPricingMode.CUSTOM
            ),
            "available_extras": available_extras,
            "category_deposit": reservation.car.category.deposit,
            "can_convert_to_rental": (
                reservation.status == ReservationStatus.CONFIRMED
                and reservation.price_lines.exists()
                and not Rental.objects.filter(reservation_id=reservation.pk).exists()
            ),
        },
    )


@staff_required
def reservation_recalculate_price(request: HttpRequest, pk: int) -> HttpResponse:
    reservation = get_reservation_by_id(pk)
    if reservation is None:
        messages.error(request, "Nie znaleziono rezerwacji.")
        return redirect("bookings:reservation_list")

    if not PriceSnapshotService.can_recalculate(reservation):
        messages.error(request, "Ceny nie mozna przeliczyc w tym statusie.")
        return redirect("bookings:reservation_detail", pk=pk)

    if request.method == "POST":
        extra_codes = request.POST.getlist("extra_codes")
        try:
            PriceSnapshotService.freeze(
                reservation,
                extra_codes=extra_codes,
                replace=True,
            )
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(request, "Przeliczono rozpis cen.")
    return redirect("bookings:reservation_detail", pk=pk)


@staff_required
def reservation_create(request: HttpRequest) -> HttpResponse:
    initial: dict = {}
    customer_id = request.GET.get("customer")
    if customer_id and customer_id.isdigit():
        initial["customer"] = int(customer_id)

    form = ReservationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            pl = form.cleaned_data.get("price_list")
            reservation = ReservationService.create(
                customer_id=form.cleaned_data["customer"].pk,
                car_id=form.cleaned_data["car"].pk,
                start_at=form.cleaned_data["start_at"],
                end_at=form.cleaned_data["end_at"],
                status=form.cleaned_data["status"],
                notes=form.cleaned_data.get("notes", ""),
                created_by_id=request.user.pk,
                pricing_mode=form.cleaned_data["pricing_mode"],
                price_list_id=pl.pk if pl else None,
                custom_total=form.cleaned_data.get("custom_total"),
            )
        except ValidationError as exc:
            _add_validation_errors_to_form(form, exc)
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, f"Utworzono rezerwacje #{reservation.pk}.")
            return redirect("bookings:reservation_detail", pk=reservation.pk)

    return render(
        request,
        "bookings/reservation_form.html",
        {"form": form, "title": "Nowa rezerwacja"},
    )


@staff_required
def reservation_edit(request: HttpRequest, pk: int) -> HttpResponse:
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.is_terminal:
        messages.error(request, "Rezerwacji w statusie koncowym nie mozna edytowac.")
        return redirect("bookings:reservation_detail", pk=pk)

    form = ReservationForm(request.POST or None, instance=reservation)
    if request.method == "POST" and form.is_valid():
        status = (
            form.cleaned_data["status"]
            if not form.fields["status"].disabled
            else reservation.status
        )
        try:
            pl = form.cleaned_data.get("price_list")
            ReservationService.update(
                reservation,
                customer_id=form.cleaned_data["customer"].pk,
                car_id=form.cleaned_data["car"].pk,
                start_at=form.cleaned_data["start_at"],
                end_at=form.cleaned_data["end_at"],
                status=status,
                notes=form.cleaned_data.get("notes", ""),
                pricing_mode=form.cleaned_data["pricing_mode"],
                price_list_id=pl.pk if pl else None,
                custom_total=form.cleaned_data.get("custom_total"),
            )
        except ValidationError as exc:
            _add_validation_errors_to_form(form, exc)
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Zapisano zmiany rezerwacji.")
            return redirect("bookings:reservation_detail", pk=reservation.pk)

    return render(
        request,
        "bookings/reservation_form.html",
        {
            "form": form,
            "title": f"Edycja rezerwacji #{reservation.pk}",
            "reservation": reservation,
        },
    )


@staff_required
def reservation_expire(request: HttpRequest, pk: int) -> HttpResponse:
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == "POST":
        try:
            ReservationService.expire(reservation)
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(request, "Oznaczono rezerwacje jako wygasla.")
    return redirect("bookings:reservation_detail", pk=pk)


@staff_required
def reservation_confirm(request: HttpRequest, pk: int) -> HttpResponse:
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == "POST":
        try:
            ReservationService.confirm(reservation)
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(request, "Potwierdzono rezerwacje.")
    return redirect("bookings:reservation_detail", pk=pk)


@staff_required
def reservation_cancel(request: HttpRequest, pk: int) -> HttpResponse:
    reservation = get_object_or_404(Reservation, pk=pk)
    form = ReservationCancelForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            ReservationService.cancel(
                reservation,
                reason=form.cleaned_data.get("reason", ""),
            )
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
            return redirect("bookings:reservation_detail", pk=pk)
        messages.success(request, "Anulowano rezerwacje.")
        return redirect("bookings:reservation_detail", pk=pk)

    return render(
        request,
        "bookings/reservation_cancel.html",
        {"reservation": reservation, "form": form},
    )


@staff_required
def reservation_convert_to_rental(request: HttpRequest, pk: int) -> HttpResponse:
    reservation = get_reservation_by_id(pk)
    if reservation is None:
        messages.error(request, "Nie znaleziono rezerwacji.")
        return redirect("bookings:reservation_list")
    if request.method == "POST":
        try:
            rental = ReservationService.convert_to_rental(
                reservation,
                created_by_id=request.user.pk,
            )
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
            return redirect("bookings:reservation_detail", pk=pk)
        messages.success(request, f"Utworzono wynajem #{rental.pk}.")
        return redirect("bookings:rental_detail", pk=rental.pk)
    return redirect("bookings:reservation_detail", pk=pk)


# --- Wynajmy ---


@staff_required
def rental_list(request: HttpRequest) -> HttpResponse:
    status_filter = request.GET.get("status", "").strip()
    rentals = list_rentals(status=status_filter or None)
    return render(
        request,
        "bookings/rental_list.html",
        {
            "rentals": rentals,
            "status_filter": status_filter,
            "status_choices": RentalStatus.choices,
        },
    )


@staff_required
def rental_detail(request: HttpRequest, pk: int) -> HttpResponse:
    rental = get_rental_by_id(pk)
    if rental is None:
        messages.error(request, "Nie znaleziono wynajmu.")
        return redirect("bookings:rental_list")
    reservation = rental.reservation
    payment_summary = get_rental_payment_summary(rental.pk)
    return render(
        request,
        "bookings/rental_detail.html",
        {
            "rental": rental,
            "reservation": reservation,
            "price_total": PriceSnapshotService.reservation_total(reservation),
            "payment_summary": payment_summary,
            "documents": list_documents(rental_id=rental.pk),
        },
    )


def _rental_action_redirect(
    request: HttpRequest,
    rental: Rental,
    *,
    success_message: str,
    action,
) -> HttpResponse:
    if request.method == "POST":
        try:
            action(rental)
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(request, success_message)
    return redirect("bookings:rental_detail", pk=rental.pk)


@staff_required
def rental_start(request: HttpRequest, pk: int) -> HttpResponse:
    rental = get_object_or_404(Rental, pk=pk)
    return _rental_action_redirect(
        request,
        rental,
        success_message="Rozpoczeto wynajem (wydanie pojazdu).",
        action=RentalService.start,
    )


@staff_required
def rental_return(request: HttpRequest, pk: int) -> HttpResponse:
    rental = get_object_or_404(Rental, pk=pk)
    return _rental_action_redirect(
        request,
        rental,
        success_message="Zarejestrowano zwrot pojazdu.",
        action=RentalService.mark_returned,
    )


@staff_required
def rental_close(request: HttpRequest, pk: int) -> HttpResponse:
    rental = get_object_or_404(Rental, pk=pk)
    return _rental_action_redirect(
        request,
        rental,
        success_message="Zamknieto wynajem.",
        action=RentalService.close,
    )


@staff_required
def rental_cancel(request: HttpRequest, pk: int) -> HttpResponse:
    rental = get_object_or_404(Rental, pk=pk)
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        try:
            RentalService.cancel(rental, reason=reason)
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(request, "Anulowano wynajem.")
    return redirect("bookings:rental_detail", pk=pk)


# --- Klienci ---


@staff_required
def customer_list(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("q", "").strip()
    customers = list_customers(search=search or None)
    return render(
        request,
        "bookings/customer_list.html",
        {
            "customers": customers,
            "search": search,
        },
    )


@staff_required
def customer_detail(request: HttpRequest, pk: int) -> HttpResponse:
    customer = get_customer_by_id(pk)
    if customer is None:
        messages.error(request, "Nie znaleziono klienta.")
        return redirect("bookings:customer_list")
    return render(
        request,
        "bookings/customer_detail.html",
        {"customer": customer},
    )


@staff_required
def customer_create(request: HttpRequest) -> HttpResponse:
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        messages.success(request, f"Dodano klienta {customer.full_name}.")
        return redirect("bookings:customer_detail", pk=customer.pk)
    return render(
        request,
        "bookings/customer_form.html",
        {"form": form, "title": "Nowy klient"},
    )


@staff_required
def customer_edit(request: HttpRequest, pk: int) -> HttpResponse:
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Zapisano zmiany klienta.")
        return redirect("bookings:customer_detail", pk=customer.pk)
    return render(
        request,
        "bookings/customer_form.html",
        {
            "form": form,
            "title": f"Edycja — {customer.full_name}",
            "customer": customer,
        },
    )


@staff_required
def customer_delete(request: HttpRequest, pk: int) -> HttpResponse:
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        name = customer.full_name
        customer.delete()
        messages.success(request, f"Usunieto klienta {name}.")
        return redirect("bookings:customer_list")
    return render(
        request,
        "bookings/customer_confirm_delete.html",
        {"customer": customer},
    )
