from __future__ import annotations

from uuid import UUID

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.permissions import customer_required
from apps.documents.selectors.document import list_documents
from apps.website.services.customer_portal import CustomerPortalService


def _download_filename(document) -> str:
    if document.title:
        stem = document.title.replace("/", "-")
    else:
        stem = document.get_document_type_display()
    return f"{stem}.pdf"


def _portal_context(request: HttpRequest) -> dict | None:
    customer = CustomerPortalService.resolve_customer(request.user)
    if customer is None:
        return None
    return {"customer": customer}


@customer_required
def portal_home(request: HttpRequest) -> HttpResponse:
    context = _portal_context(request)
    if context is None:
        return render(
            request,
            "website/portal/home.html",
            {"profile_missing": True},
        )
    customer = context["customer"]
    return render(
        request,
        "website/portal/home.html",
        {
            **context,
            "reservations": CustomerPortalService.list_reservations(
                customer_id=customer.pk,
            )[:5],
            "documents": CustomerPortalService.list_documents(customer_id=customer.pk),
        },
    )


@customer_required
def reservation_list(request: HttpRequest) -> HttpResponse:
    context = _portal_context(request)
    if context is None:
        messages.error(request, "Brak profilu klienta powiazanego z kontem.")
        return redirect("customer_portal:home")
    customer = context["customer"]
    return render(
        request,
        "website/portal/reservation_list.html",
        {
            **context,
            "reservations": CustomerPortalService.list_reservations(
                customer_id=customer.pk,
            ),
        },
    )


@customer_required
def reservation_detail(request: HttpRequest, reservation_id: int) -> HttpResponse:
    context = _portal_context(request)
    if context is None:
        messages.error(request, "Brak profilu klienta powiazanego z kontem.")
        return redirect("customer_portal:home")
    customer = context["customer"]
    reservation = CustomerPortalService.get_reservation(
        reservation_id=reservation_id,
        customer_id=customer.pk,
    )
    if reservation is None:
        messages.error(request, "Nie znaleziono rezerwacji.")
        return redirect("customer_portal:reservation_list")
    documents = []
    try:
        rental_id = reservation.rental.pk
    except ObjectDoesNotExist:
        pass
    else:
        documents = list(list_documents(rental_id=rental_id))
    return render(
        request,
        "website/portal/reservation_detail.html",
        {
            **context,
            "reservation": reservation,
            "documents": documents,
        },
    )


@customer_required
def document_download(request: HttpRequest, document_uuid: UUID) -> FileResponse:
    context = _portal_context(request)
    if context is None:
        raise Http404("Nie znaleziono dokumentu.")
    customer = context["customer"]
    document = CustomerPortalService.get_downloadable_document(
        document_uuid=document_uuid,
        customer_id=customer.pk,
    )
    if document is None:
        raise Http404("Nie znaleziono dokumentu.")

    file_handle = document.file.open("rb")
    filename = _download_filename(document)
    response = FileResponse(
        file_handle,
        content_type=document.content_type,
        as_attachment=False,
        filename=filename,
    )
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
