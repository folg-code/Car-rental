from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.fleet.models import Car, CarDocument, CarImage
from config.upload_validation import validate_document_upload, validate_image_upload


class CarMediaService:
    @staticmethod
    @transaction.atomic
    def add_image(
        car: Car,
        *,
        image,
        caption: str = "",
        is_primary: bool = False,
    ) -> CarImage:
        validate_image_upload(image)
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
        validate_document_upload(file)
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
