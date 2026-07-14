from datetime import date, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.fleet.models import Car, CarCategory, CarDocument, CarDocumentType, CarStatus
from apps.fleet.selectors.documents import (
    count_expiring_car_documents,
    get_expiring_car_documents,
)


def _sample_file(name: str = "doc.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"%PDF-1.4 test", content_type="application/pdf")


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-docs")


@pytest.fixture
def active_car(category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="DOC001",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture
def inactive_car(category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="DOC002",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.INACTIVE,
    )


def _create_document(
    car: Car,
    *,
    document_type: str,
    valid_until: date | None,
) -> CarDocument:
    return CarDocument.objects.create(
        car=car,
        document_type=document_type,
        file=_sample_file(),
        valid_until=valid_until,
    )


@pytest.mark.django_db
class TestExpiringCarDocumentsSelector:
    def test_counts_insurance_expiring_within_window(self, active_car: Car) -> None:
        as_of = date(2026, 7, 1)
        _create_document(
            active_car,
            document_type=CarDocumentType.INSURANCE,
            valid_until=as_of + timedelta(days=15),
        )

        assert count_expiring_car_documents(as_of=as_of) == 1
        assert get_expiring_car_documents(as_of=as_of).count() == 1

    def test_counts_expired_inspection(self, active_car: Car) -> None:
        as_of = date(2026, 7, 1)
        _create_document(
            active_car,
            document_type=CarDocumentType.INSPECTION,
            valid_until=as_of - timedelta(days=1),
        )

        assert count_expiring_car_documents(as_of=as_of) == 1

    def test_excludes_document_beyond_window(self, active_car: Car) -> None:
        as_of = date(2026, 7, 1)
        _create_document(
            active_car,
            document_type=CarDocumentType.INSURANCE,
            valid_until=as_of + timedelta(days=31),
        )

        assert count_expiring_car_documents(as_of=as_of) == 0

    def test_excludes_registration_and_other_types(self, active_car: Car) -> None:
        as_of = date(2026, 7, 1)
        horizon = as_of + timedelta(days=10)
        _create_document(
            active_car,
            document_type=CarDocumentType.REGISTRATION,
            valid_until=horizon,
        )
        _create_document(
            active_car,
            document_type=CarDocumentType.OTHER,
            valid_until=horizon,
        )

        assert count_expiring_car_documents(as_of=as_of) == 0

    def test_excludes_inactive_car(self, inactive_car: Car) -> None:
        as_of = date(2026, 7, 1)
        _create_document(
            inactive_car,
            document_type=CarDocumentType.INSURANCE,
            valid_until=as_of + timedelta(days=5),
        )

        assert count_expiring_car_documents(as_of=as_of) == 0

    def test_excludes_missing_valid_until(self, active_car: Car) -> None:
        as_of = date(2026, 7, 1)
        _create_document(
            active_car,
            document_type=CarDocumentType.INSURANCE,
            valid_until=None,
        )

        assert count_expiring_car_documents(as_of=as_of) == 0
