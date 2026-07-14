from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.constants import HANDOVER_PROTOCOL_PDF_TEMPLATE
from apps.documents.dto.protocol import HandoverDocumentData, image_field_to_uri
from apps.documents.selectors.protocol_data import (
    build_handover_document_data,
    build_return_document_data,
    get_handover_document_data,
)
from apps.documents.services.pdf_renderer import PdfRenderer
from apps.documents.tests.conftest import MINIMAL_PNG_BYTES, tiny_signature_image
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.fleet.services.damage import DamageService
from apps.operations.models import HandoverProtocol
from apps.operations.services.handover import HandoverService
from apps.operations.services.return_workflow import ReturnService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV", slug="suv-doc-dto", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Doc DTO",
        slug="doc-dto",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("100"))
    return pl


@pytest.fixture
def scheduled_rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@doc-dto.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1DTO01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
    )
    start = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)


@pytest.fixture
def completed_handover(scheduled_rental) -> HandoverProtocol:
    car = scheduled_rental.reservation.car
    DamageService.report_damage(
        car=car,
        description="Rysa na drzwiach",
        location="lewe przednie",
        severity="minor",
    )
    return HandoverService.complete_handover(
        scheduled_rental.pk,
        mileage=10_200,
        fuel_level_percent=90,
        signer_name="Jan Kowalski",
        signature_image=tiny_signature_image(),
        notes="Stan OK.",
    )


@pytest.mark.django_db
class TestHandoverDocumentData:
    def test_build_from_completed_handover(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        data = build_handover_document_data(completed_handover)
        assert isinstance(data, HandoverDocumentData)
        assert data.rental_id == completed_handover.rental_id
        assert data.customer_name == "Jan Kowalski"
        assert data.registration_number == "KR1DTO01"
        assert data.mileage == 10_200
        assert data.fuel_level_percent == 90
        assert data.notes == "Stan OK."
        assert len(data.damages) == 1
        assert data.damages[0].description == "Rysa na drzwiach"
        assert data.signature_name == "Jan Kowalski"

    def test_rejects_incomplete_handover(self, scheduled_rental) -> None:
        handover = HandoverProtocol.objects.create(
            rental=scheduled_rental,
            mileage=10_100,
            fuel_level_percent=100,
        )
        with pytest.raises(ValidationError, match="zakonczonego"):
            build_handover_document_data(handover)

    def test_damage_text_unchanged_after_fleet_edit(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        snap = completed_handover.damage_snapshots.first()
        assert snap is not None
        damage = snap.source_damage
        assert damage is not None

        data_before = build_handover_document_data(completed_handover)
        damage.description = "Opis zmieniony w flocie — nie powinien trafic do PDF"
        damage.save(update_fields=["description"])

        data_after = get_handover_document_data(completed_handover.pk)
        assert data_after.damages[0].description == data_before.damages[0].description
        assert data_after.damages[0].description != damage.description

    def test_as_template_context_renders_pdf(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        data = build_handover_document_data(completed_handover)
        pdf_bytes = PdfRenderer.render_template(
            HANDOVER_PROTOCOL_PDF_TEMPLATE,
            data.as_template_context(),
        )
        assert PdfRenderer.is_pdf(pdf_bytes)


@pytest.mark.django_db
class TestReturnDocumentData:
    def test_build_from_completed_return(
        self,
        completed_handover: HandoverProtocol,
    ) -> None:
        scheduled_rental = completed_handover.rental
        return_protocol = ReturnService.complete_return(
            scheduled_rental.pk,
            mileage=10_450,
            fuel_level_percent=70,
            signer_name="Jan Kowalski",
            signature_image=tiny_signature_image("ret.png"),
            notes="Zwrot bez problemow.",
        )
        data = build_return_document_data(return_protocol)
        assert data.handover_mileage == 10_200
        assert data.handover_fuel_level_percent == 90
        assert data.mileage == 10_450
        assert data.mileage_driven == 250
        assert data.notes == "Zwrot bez problemow."
        assert data.signature_name == "Jan Kowalski"


class TestImageFieldToUri:
    def test_returns_data_uri_for_local_file(self, tmp_path) -> None:
        file_path = tmp_path / "sig.png"
        file_path.write_bytes(MINIMAL_PNG_BYTES)

        class _ImageField:
            name = str(file_path)

            @property
            def path(self) -> str:
                return str(file_path)

        uri = image_field_to_uri(_ImageField())
        assert uri is not None
        assert uri.startswith("data:image/png;base64,")
        assert not uri.startswith("file:")
