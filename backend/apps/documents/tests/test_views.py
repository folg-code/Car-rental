import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.documents.models import Document, DocumentType
from apps.operations.services.handover import HandoverService


def _tiny_image(name: str = "sig.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        b"\x89PNG\r\n\x1a\n",
        content_type="image/png",
    )


@pytest.fixture
def staff_user(db):
    return UserService.create_user(
        username="staff-docs",
        password="test-pass-123",
        role=UserRole.EMPLOYEE,
    )


@pytest.fixture
def staff_client(staff_user) -> Client:
    client = Client()
    client.force_login(staff_user)
    return client


@pytest.fixture
def handover_document(scheduled_rental) -> Document:
    HandoverService.complete_handover(
        scheduled_rental.pk,
        mileage=10_500,
        fuel_level_percent=90,
        signer_name="Jan Kowalski",
        signature_image=_tiny_image(),
        notes="",
        photo_files=[],
        new_damages=[],
        performed_by_id=None,
    )
    return Document.objects.get(
        rental_id=scheduled_rental.pk,
        document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
    )


@pytest.mark.django_db
class TestDocumentPanelViews:
    def test_anonymous_redirects_to_login(self, handover_document) -> None:
        client = Client()
        response = client.get(reverse("documents:home"))
        assert response.status_code == 302
        assert "logowanie" in response.url

    def test_staff_can_list_documents(self, staff_client, handover_document) -> None:
        response = staff_client.get(reverse("documents:home"))
        assert response.status_code == 200
        assert (
            handover_document.get_document_type_display() in response.content.decode()
        )

    def test_staff_can_list_rental_documents(
        self, staff_client, handover_document, scheduled_rental
    ) -> None:
        url = reverse("documents:rental", kwargs={"rental_id": scheduled_rental.pk})
        response = staff_client.get(url)
        assert response.status_code == 200
        assert str(scheduled_rental.pk) in response.content.decode()

    def test_staff_can_download_pdf(self, staff_client, handover_document) -> None:
        url = reverse(
            "documents:download",
            kwargs={"document_uuid": handover_document.uuid},
        )
        response = staff_client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        body = b"".join(response.streaming_content)
        assert body.startswith(b"%PDF")

    def test_anonymous_cannot_download_pdf(self, handover_document) -> None:
        client = Client()
        url = reverse(
            "documents:download",
            kwargs={"document_uuid": handover_document.uuid},
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "logowanie" in response.url

    def test_download_unknown_uuid_returns_404(self, staff_client) -> None:
        url = reverse(
            "documents:download",
            kwargs={"document_uuid": "00000000-0000-0000-0000-000000000000"},
        )
        response = staff_client.get(url)
        assert response.status_code == 404

    def test_rental_documents_unknown_rental_redirects(self, staff_client) -> None:
        response = staff_client.get(
            reverse("documents:rental", kwargs={"rental_id": 999_999})
        )
        assert response.status_code == 302
        assert response.url == reverse("documents:home")
