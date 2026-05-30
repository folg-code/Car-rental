import pytest
from django.conf import settings
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import Document, DocumentType


@pytest.mark.django_db
class TestPrivateDocumentStorage:
    def test_storage_location_outside_media_root(self) -> None:
        storage = storages["private_documents"]
        assert storage.location == str(settings.DOCUMENTS_PRIVATE_ROOT)
        assert str(settings.DOCUMENTS_PRIVATE_ROOT) != str(settings.MEDIA_ROOT)
        assert str(settings.MEDIA_ROOT) not in storage.location

    def test_url_not_public(self) -> None:
        storage = storages["private_documents"]
        with pytest.raises(NotImplementedError, match="Prywatne dokumenty"):
            storage.url("handover_protocol_pdf/2026/05/test.pdf")

    def test_saved_file_under_private_root(
        self,
        scheduled_rental,
    ) -> None:
        from apps.operations.models import HandoverProtocol

        handover = HandoverProtocol.objects.create(
            rental=scheduled_rental,
            mileage=10_000,
            fuel_level_percent=100,
            completed_at="2026-05-20T10:00:00Z",
        )
        pdf = SimpleUploadedFile(
            "protokol.pdf",
            b"%PDF-1.4 private storage test",
            content_type="application/pdf",
        )
        doc = Document.objects.create(
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            rental=scheduled_rental,
            handover_protocol=handover,
            file=pdf,
            file_size_bytes=pdf.size,
        )
        path = settings.DOCUMENTS_PRIVATE_ROOT / doc.file.name
        assert path.is_file()
        assert str(settings.MEDIA_ROOT) not in str(path.resolve())
