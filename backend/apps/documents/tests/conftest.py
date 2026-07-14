import base64

from django.core.files.uploadedfile import SimpleUploadedFile

# 1x1 px PNG — poprawny obraz dla WeasyPrint w CI (nie sam naglowek PNG).
MINIMAL_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AAwMCAO+"
    "X9qfAAAAABJRU5ErkJggg=="
)


def tiny_signature_image(name: str = "sig.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        MINIMAL_PNG_BYTES,
        content_type="image/png",
    )
