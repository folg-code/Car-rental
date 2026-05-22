from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import staff_required
from apps.bookings.forms import CustomerForm
from apps.bookings.models import Customer
from apps.bookings.selectors.customer import get_customer_by_id, list_customers


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
