from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.fleet.models import Car, CarDocument, CarImage

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)


class CarMediaService:
    @staticmethod
    def _validate_upload_size(uploaded_file) -> None:
        if uploaded_file.size > MAX_UPLOAD_BYTES:
            raise ValidationError(
                f"Plik jest za duzy (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)."
            )

    @staticmethod
    def _validate_image(uploaded_file) -> None:
        CarMediaService._validate_upload_size(uploaded_file)
        content_type = getattr(uploaded_file, "content_type", "") or ""
        if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise ValidationError("Dozwolone formaty zdjec: JPEG, PNG, WebP, GIF.")

    @staticmethod
    @transaction.atomic
    def add_image(
        car: Car,
        *,
        image,
        caption: str = "",
        is_primary: bool = False,
    ) -> CarImage:
        CarMediaService._validate_image(image)
        if is_primary:
            CarImage.objects.filter(car=car, is_primary=True).update(is_primary=False)
        elif not CarImage.objects.filter(car=car).exists():
            is_primary = True

        return CarImage.objects.create(
            car=car,
            image=image,
            caption=caption.strip(),
            is_primary=is_primary,
        )

    @staticmethod
    @transaction.atomic
    def set_primary_image(car: Car, image_id: int) -> CarImage:
        car_image = CarImage.objects.filter(pk=image_id, car=car).first()
        if car_image is None:
            raise ValidationError("Nie znaleziono zdjecia dla tego pojazdu.")
        CarImage.objects.filter(car=car, is_primary=True).update(is_primary=False)
        car_image.is_primary = True
        car_image.save(update_fields=["is_primary"])
        return car_image

    @staticmethod
    def delete_image(car: Car, image_id: int) -> None:
        car_image = CarImage.objects.filter(pk=image_id, car=car).first()
        if car_image is None:
            raise ValidationError("Nie znaleziono zdjecia dla tego pojazdu.")
        was_primary = car_image.is_primary
        car_image.delete()
        if was_primary:
            next_image = (
                CarImage.objects.filter(car=car).order_by("-uploaded_at").first()
            )
            if next_image is not None:
                next_image.is_primary = True
                next_image.save(update_fields=["is_primary"])

    @staticmethod
    def add_document(
        car: Car,
        *,
        file,
        document_type: str,
        valid_from=None,
        valid_until=None,
        notes: str = "",
    ) -> CarDocument:
        CarMediaService._validate_upload_size(file)
        return CarDocument.objects.create(
            car=car,
            file=file,
            document_type=document_type,
            valid_from=valid_from,
            valid_until=valid_until,
            notes=notes.strip(),
        )

    @staticmethod
    def delete_document(car: Car, document_id: int) -> None:
        document = CarDocument.objects.filter(pk=document_id, car=car).first()
        if document is None:
            raise ValidationError("Nie znaleziono dokumentu dla tego pojazdu.")
        document.delete()
