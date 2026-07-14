from __future__ import annotations

import os
from collections.abc import Iterable

from django.conf import settings
from django.core.exceptions import ValidationError

DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024

ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
ALLOWED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})

ALLOWED_DOCUMENT_CONTENT_TYPES = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)
ALLOWED_DOCUMENT_EXTENSIONS = frozenset({".pdf", ".jpg", ".jpeg", ".png", ".webp"})

MAX_UPLOAD_BYTES = DEFAULT_MAX_UPLOAD_BYTES


def get_max_upload_bytes() -> int:
    return int(getattr(settings, "UPLOAD_MAX_BYTES", DEFAULT_MAX_UPLOAD_BYTES))


def _file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def _content_type(uploaded_file) -> str:
    return (getattr(uploaded_file, "content_type", "") or "").lower()


def _validate_allowed_type(
    uploaded_file,
    *,
    allowed_content_types: frozenset[str],
    allowed_extensions: frozenset[str],
    label: str,
) -> None:
    content_type = _content_type(uploaded_file)
    extension = _file_extension(getattr(uploaded_file, "name", "") or "")

    if content_type and content_type in allowed_content_types:
        return
    if extension and extension in allowed_extensions:
        return

    raise ValidationError(label)


def validate_upload_size(uploaded_file) -> None:
    size = getattr(uploaded_file, "size", None)
    if size is None:
        return
    max_bytes = get_max_upload_bytes()
    if size > max_bytes:
        raise ValidationError(
            f"Plik jest za duzy (max {max_bytes // (1024 * 1024)} MB)."
        )


def validate_image_upload(uploaded_file) -> None:
    validate_upload_size(uploaded_file)
    _validate_allowed_type(
        uploaded_file,
        allowed_content_types=ALLOWED_IMAGE_CONTENT_TYPES,
        allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
        label="Dozwolone formaty zdjec: JPEG, PNG, WebP, GIF.",
    )


def validate_document_upload(uploaded_file) -> None:
    validate_upload_size(uploaded_file)
    _validate_allowed_type(
        uploaded_file,
        allowed_content_types=ALLOWED_DOCUMENT_CONTENT_TYPES,
        allowed_extensions=ALLOWED_DOCUMENT_EXTENSIONS,
        label="Dozwolone formaty dokumentow: PDF, JPEG, PNG, WebP.",
    )


def validate_image_uploads(uploaded_files: Iterable) -> None:
    for uploaded_file in uploaded_files:
        if uploaded_file:
            validate_image_upload(uploaded_file)
