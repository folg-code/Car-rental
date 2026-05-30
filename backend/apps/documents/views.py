from uuid import UUID

from django.contrib import messages
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.permissions import staff_required
from apps.bookings.selectors.rental import get_rental_by_id
from apps.documents.selectors.document import (
    get_document_by_uuid,
    list_documents,
)


def _download_filename(document) -> str:
    if document.title:
        stem = document.title.replace("/", "-")
    else:
        stem = document.get_document_type_display()
    return f"{stem}.pdf"


@staff_required
def document_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "documents/document_list.html",
        {"documents": list_documents()},
    )


@staff_required
def rental_documents(request: HttpRequest, rental_id: int) -> HttpResponse:
    rental = get_rental_by_id(rental_id)
    if rental is None:
        messages.error(request, "Nie znaleziono wynajmu.")
        return redirect("documents:home")
    return render(
        request,
        "documents/document_list.html",
        {
            "documents": list_documents(rental_id=rental_id),
            "rental": rental,
            "reservation": rental.reservation,
        },
    )


@staff_required
def document_download(request: HttpRequest, document_uuid: UUID) -> FileResponse:
    document = get_document_by_uuid(document_uuid)
    if document is None or not document.file:
        raise Http404("Nie znaleziono dokumentu.")

    file_handle = document.file.open("rb")
    response = FileResponse(
        file_handle,
        content_type=document.content_type,
        as_attachment=False,
        filename=_download_filename(document),
    )
    response["Content-Disposition"] = (
        f'inline; filename="{_download_filename(document)}"'
    )
    return response
