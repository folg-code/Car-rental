from datetime import date, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.dashboard.selectors.fleet_alerts import (
    count_fleet_expiry_alerts,
    list_fleet_expiry_alerts,
)
from apps.dashboard.selectors.metrics import get_dashboard_metrics
from apps.fleet.models import Car, CarCategory, CarDocument, CarDocumentType, CarStatus


def _sample_file() -> SimpleUploadedFile:
    return SimpleUploadedFile(
        "doc.pdf", b"%PDF-1.4 test", content_type="application/pdf"
    )


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-alerts")


@pytest.fixture
def active_car(category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="ALERT01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestFleetAlertsDashboardSelector:
    def test_count_and_list_expiry_alerts(self, active_car: Car) -> None:
        as_of = date(2026, 7, 1)
        doc = CarDocument.objects.create(
            car=active_car,
            document_type=CarDocumentType.INSPECTION,
            file=_sample_file(),
            valid_until=as_of + timedelta(days=7),
        )

        assert count_fleet_expiry_alerts(as_of=as_of) == 1
        alerts = list_fleet_expiry_alerts(as_of=as_of)
        assert len(alerts) == 1
        assert alerts[0].pk == doc.pk

    def test_metrics_include_expiring_fleet_documents(self, active_car: Car) -> None:
        CarDocument.objects.create(
            car=active_car,
            document_type=CarDocumentType.INSURANCE,
            file=_sample_file(),
            valid_until=date.today() + timedelta(days=14),
        )

        metrics = get_dashboard_metrics()
        assert metrics.expiring_fleet_documents == 1
