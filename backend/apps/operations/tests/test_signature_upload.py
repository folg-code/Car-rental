"""Testy dekodowania podpisu z canvas (data URL)."""

import base64

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.operations.forms import HandoverProtocolForm
from apps.operations.services.signature_upload import signature_file_from_form


def _tiny_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )


@pytest.mark.django_db
class TestSignatureUpload:
    def test_prefers_uploaded_file(self) -> None:
        uploaded = SimpleUploadedFile(
            "sig.png", _tiny_png_bytes(), content_type="image/png"
        )
        result = signature_file_from_form(
            uploaded=uploaded,
            data_url="data:image/png;base64,AAAA",
        )
        assert result is uploaded

    def test_decodes_canvas_data_url(self) -> None:
        data_url = (
            "data:image/png;base64," + base64.b64encode(_tiny_png_bytes()).decode()
        )
        result = signature_file_from_form(uploaded=None, data_url=data_url)
        assert result is not None
        assert result.name.endswith(".png")
        assert result.read() == _tiny_png_bytes()

    def test_rejects_invalid_data_url(self) -> None:
        assert signature_file_from_form(uploaded=None, data_url="not-an-image") is None


class TestHandoverProtocolFormSignature:
    def test_requires_signature(self) -> None:
        form = HandoverProtocolForm(
            data={
                "mileage": 100,
                "fuel_level_percent": 50,
                "signer_name": "Jan",
                "signature_data_url": "",
            }
        )
        assert form.is_valid() is False
        assert form.non_field_errors()

    def test_accepts_canvas_data_url(self) -> None:
        data_url = (
            "data:image/png;base64," + base64.b64encode(_tiny_png_bytes()).decode()
        )
        form = HandoverProtocolForm(
            data={
                "mileage": 100,
                "fuel_level_percent": 50,
                "signer_name": "Jan",
                "signature_data_url": data_url,
            }
        )
        assert form.is_valid() is True
