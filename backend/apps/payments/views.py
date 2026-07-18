from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import owner_or_manager_required, staff_required
from apps.bookings.models import Rental
from apps.bookings.selectors.rental import get_rental_by_id
from apps.payments.forms import PaymentRecordForm
from apps.payments.models import PaymentType
from apps.payments.selectors.payment import (
    get_rental_payment_summary,
    list_payments,
)
from apps.payments.services.payment import PaymentService


@staff_required
def payment_list(request: HttpRequest) -> HttpResponse:
    payments = list_payments(limit=100)
    return render(
        request,
        "payments/payment_list.html",
        {"payments": payments},
    )


@staff_required
def rental_payments(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    if rental is None:
        messages.error(request, "Nie znaleziono wynajmu.")
        return redirect("bookings:rental_list")

    summary = get_rental_payment_summary(rental_id)
    form = PaymentRecordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payment_type = form.cleaned_data["payment_type"]
        try:
            if payment_type == PaymentType.DEPOSIT:
                PaymentService.record_deposit(
                    rental_id=rental_id,
                    amount=form.cleaned_data["amount"],
                    method=form.cleaned_data["method"],
                    paid_at=form.cleaned_data.get("paid_at"),
                    notes=form.cleaned_data.get("notes", ""),
                    recorded_by_id=request.user.pk,
                )
            elif payment_type == PaymentType.REFUND:
                PaymentService.refund_deposit(
                    rental_id=rental_id,
                    amount=form.cleaned_data["amount"],
                    method=form.cleaned_data["method"],
                    paid_at=form.cleaned_data.get("paid_at"),
                    notes=form.cleaned_data.get("notes", ""),
                    recorded_by_id=request.user.pk,
                )
            else:
                PaymentService.record_payment(
                    rental_id=rental_id,
                    amount=form.cleaned_data["amount"],
                    payment_type=payment_type,
                    method=form.cleaned_data["method"],
                    paid_at=form.cleaned_data.get("paid_at"),
                    notes=form.cleaned_data.get("notes", ""),
                    recorded_by_id=request.user.pk,
                )
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, errs in exc.message_dict.items():
                    for err in errs:
                        form.add_error(field if field != "__all__" else None, err)
            elif exc.messages:
                form.add_error(None, exc.messages[0])
            else:
                form.add_error(None, str(exc))
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Zarejestrowano płatność.")
            return redirect("payments:rental_payments", rental_id=rental_id)

    if not form.is_bound and summary:
        if summary.get("extra_charges_due", 0) > 0:
            form.fields["amount"].initial = summary["extra_charges_due"]
            form.fields["payment_type"].initial = PaymentType.EXTRA_CHARGE
        elif summary.get("rental_fee_due", 0) > 0:
            form.fields["amount"].initial = summary["rental_fee_due"]
            form.fields["payment_type"].initial = PaymentType.RENTAL_FEE

    return render(
        request,
        "payments/rental_payments.html",
        {
            "rental": rental,
            "reservation": rental.reservation,
            "summary": summary,
            "payments": list_payments(rental_id=rental_id),
            "form": form,
        },
    )


@staff_required
def record_deposit_quick(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_object_or_404(Rental, pk=rental_id)
    if request.method == "POST":
        try:
            PaymentService.record_deposit(
                rental_id=rental.pk,
                recorded_by_id=request.user.pk,
            )
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(
                request,
                f"Zarejestrowano kaucje {rental.deposit_amount} PLN.",
            )
    return redirect("payments:rental_payments", rental_id=rental_id)


@owner_or_manager_required
def refund_deposit_quick(request: HttpRequest, rental_id: int) -> HttpResponse:
    if request.method == "POST":
        try:
            PaymentService.refund_deposit(
                rental_id=rental_id,
                recorded_by_id=request.user.pk,
            )
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else str(exc))
        else:
            messages.success(request, "Zarejestrowano zwrot kaucji.")
    return redirect("payments:rental_payments", rental_id=rental_id)
