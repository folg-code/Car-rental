from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from config.upload_validation import (
    get_max_upload_bytes,
    validate_document_upload,
    validate_image_upload,
)


def _tiny_png() -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color="blue").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile("photo.png", buffer.read(), content_type="image/png")


@pytest.mark.django_db
class TestUploadValidation:
    def test_validate_image_upload_accepts_png(self) -> None:
        validate_image_upload(_tiny_png())

    def test_validate_image_upload_rejects_executable(self) -> None:
        invalid = SimpleUploadedFile(
            "bad.exe",
            b"MZ",
            content_type="application/x-msdownload",
        )
        with pytest.raises(ValidationError, match="Dozwolone formaty zdjec"):
            validate_image_upload(invalid)

    def test_validate_image_upload_rejects_oversized_file(self) -> None:
        huge = SimpleUploadedFile(
            "big.png",
            b"x" * (get_max_upload_bytes() + 1),
            content_type="image/png",
        )
        with pytest.raises(ValidationError, match="za duzy"):
            validate_image_upload(huge)

    def test_validate_document_upload_accepts_pdf(self) -> None:
        pdf = SimpleUploadedFile(
            "policy.pdf",
            b"%PDF-1.4 test",
            content_type="application/pdf",
        )
        validate_document_upload(pdf)

    def test_validate_document_upload_rejects_unknown_type(self) -> None:
        invalid = SimpleUploadedFile(
            "notes.txt",
            b"hello",
            content_type="text/plain",
        )
        with pytest.raises(ValidationError, match="Dozwolone formaty dokumentow"):
            validate_document_upload(invalid)
