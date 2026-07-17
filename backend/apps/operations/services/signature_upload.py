from __future__ import annotations

import base64
import re

from django.core.files.uploadedfile import SimpleUploadedFile

_DATA_URL_RE = re.compile(
    r"^data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=\s]+)$",
    re.IGNORECASE,
)


def signature_file_from_form(*, uploaded, data_url: str | None):
    """Prefer uploaded file; otherwise decode canvas data URL to PNG upload."""
    if uploaded:
        return uploaded
    raw = (data_url or "").strip()
    if not raw:
        return None
    match = _DATA_URL_RE.match(raw)
    if match is None:
        return None
    ext = match.group(1).lower()
    if ext == "jpg":
        ext = "jpeg"
    content_type = f"image/{ext}"
    try:
        payload = base64.b64decode(match.group(2), validate=True)
    except (ValueError, TypeError):
        return None
    if not payload:
        return None
    filename = f"signature.{'jpg' if ext == 'jpeg' else ext}"
    return SimpleUploadedFile(filename, payload, content_type=content_type)
