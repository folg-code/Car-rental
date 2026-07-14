from decimal import Decimal
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.fleet.models import Car, CarCategory, CarDocument, CarDocumentType, CarImage
from apps.fleet.services.car_media import CarMediaService
from config.upload_validation import get_max_upload_bytes


def _tiny_image(name: str = "car.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def _sample_pdf(name: str = "oc.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"%PDF-1.4 test", content_type="application/pdf")


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV", slug="suv-media", deposit=Decimal("500")
    )


@pytest.fixture
def car(category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="KR1MEDIA1",
        make="Skoda",
        model="Kodiaq",
        year=2023,
    )


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="fleet_media_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="fleet_media_staff", password="secure-pass-123")
    return client


@pytest.mark.django_db
class TestCarMediaService:
    def test_add_image_sets_first_as_primary(self, car: Car) -> None:
        image = CarMediaService.add_image(car, image=_tiny_image())
        assert image.is_primary is True

    def test_set_primary_image(self, car: Car) -> None:
        first = CarMediaService.add_image(car, image=_tiny_image("a.png"))
        second = CarMediaService.add_image(
            car, image=_tiny_image("b.png"), is_primary=True
        )
        first.refresh_from_db()
        assert first.is_primary is False
        assert second.is_primary is True

    def test_delete_primary_promotes_next_image(self, car: Car) -> None:
        first = CarMediaService.add_image(car, image=_tiny_image("a.png"))
        second = CarMediaService.add_image(car, image=_tiny_image("b.png"))
        CarMediaService.delete_image(car, first.pk)
        second.refresh_from_db()
        assert second.is_primary is True

    def test_rejects_oversized_file(self, car: Car) -> None:
        huge = SimpleUploadedFile(
            "big.png",
            b"x" * (get_max_upload_bytes() + 1),
            content_type="image/png",
        )
        with pytest.raises(ValidationError, match="za duzy"):
            CarMediaService.add_image(car, image=huge)

    def test_rejects_invalid_image_type(self, car: Car) -> None:
        invalid = SimpleUploadedFile(
            "script.exe",
            b"MZ",
            content_type="application/x-msdownload",
        )
        with pytest.raises(ValidationError, match="Dozwolone formaty zdjec"):
            CarMediaService.add_image(car, image=invalid)

    def test_rejects_invalid_document_type(self, car: Car) -> None:
        invalid = SimpleUploadedFile(
            "payload.exe",
            b"MZ",
            content_type="application/x-msdownload",
        )
        with pytest.raises(ValidationError, match="Dozwolone formaty dokumentow"):
            CarMediaService.add_document(
                car,
                file=invalid,
                document_type=CarDocumentType.INSURANCE,
            )

    def test_add_document(self, car: Car) -> None:
        document = CarMediaService.add_document(
            car,
            file=_sample_pdf(),
            document_type=CarDocumentType.INSURANCE,
            notes="OC 2026",
        )
        assert document.pk is not None
        assert CarDocument.objects.filter(car=car).count() == 1


@pytest.mark.django_db
class TestFleetMediaViews:
    def test_image_upload_creates_car_image(self, staff_client, car: Car) -> None:
        response = staff_client.post(
            reverse("fleet:image_upload", kwargs={"car_pk": car.pk}),
            {
                "caption": "Przod",
                "is_primary": True,
                "image": _tiny_image(),
            },
        )
        assert response.status_code == 302
        assert CarImage.objects.filter(car=car).count() == 1

    def test_document_upload_creates_car_document(self, staff_client, car: Car) -> None:
        response = staff_client.post(
            reverse("fleet:document_upload", kwargs={"car_pk": car.pk}),
            {
                "document_type": CarDocumentType.INSPECTION,
                "valid_until": "2027-01-15",
                "notes": "Przeglad OK",
                "file": _sample_pdf(),
            },
        )
        assert response.status_code == 302
        document = CarDocument.objects.get(car=car)
        assert document.document_type == CarDocumentType.INSPECTION

    def test_car_detail_shows_uploaded_media(self, staff_client, car: Car) -> None:
        CarMediaService.add_image(car, image=_tiny_image(), caption="Test")
        CarMediaService.add_document(
            car,
            file=_sample_pdf(),
            document_type=CarDocumentType.INSURANCE,
        )
        response = staff_client.get(reverse("fleet:car_detail", kwargs={"pk": car.pk}))
        assert response.status_code == 200
        assert b"Zdjecia" in response.content
        assert b"Dokumenty" in response.content
        assert CarImage.objects.filter(car=car, caption="Test").exists()

    def test_image_delete(self, staff_client, car: Car) -> None:
        image = CarMediaService.add_image(car, image=_tiny_image())
        response = staff_client.post(
            reverse(
                "fleet:image_delete", kwargs={"car_pk": car.pk, "image_pk": image.pk}
            )
        )
        assert response.status_code == 302
        assert not CarImage.objects.filter(pk=image.pk).exists()
