from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.audit.models import AuditAction, AuditLog
from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.operations.services.handover import HandoverService
from apps.payments.models import PaymentMethod, PaymentType
from apps.payments.services.payment import PaymentService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-audit",
        deposit=Decimal("500.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik audit",
        slug="test-audit",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("200.00"),
    )
    return price_list


@pytest.fixture
def rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Anna",
        last_name="Audit",
        email="anna@audit.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1AUD01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
    )
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)


@pytest.mark.django_db
class TestAuditIntegration:
    def test_confirm_reservation_writes_audit_log(
        self, db, category: CarCategory
    ) -> None:
        customer = Customer.objects.create(
            first_name="Ewa",
            last_name="Test",
            email="ewa@audit.test",
        )
        car = Car.objects.create(
            category=category,
            registration_number="KR1AUD02",
            make="Toyota",
            model="Yaris",
            year=2022,
            status=CarStatus.ACTIVE,
        )
        start = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.PENDING_PAYMENT,
        )

        ReservationService.confirm(reservation)

        assert AuditLog.objects.filter(
            action=AuditAction.RESERVATION_CONFIRMED,
            reservation_id=reservation.pk,
        ).exists()

    def test_record_payment_writes_audit_log(self, rental) -> None:
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("400.00"),
            method=PaymentMethod.CASH,
        )

        entry = AuditLog.objects.get(
            action=AuditAction.PAYMENT_RECORDED,
            rental_id=rental.pk,
        )
        assert entry.metadata["payment_type"] == PaymentType.RENTAL_FEE
        assert entry.metadata["amount"] == "400.00"

    def test_handover_writes_protocol_and_rental_audit(self, rental) -> None:
        from apps.operations.tests.test_operations import _tiny_image

        HandoverService.complete_handover(
            rental.pk,
            mileage=10_200,
            fuel_level_percent=90,
            signer_name="Jan Kowalski",
            signature_image=_tiny_image(),
            performed_by_id=None,
        )

        assert AuditLog.objects.filter(
            action=AuditAction.HANDOVER_COMPLETED,
            rental_id=rental.pk,
        ).exists()
        assert AuditLog.objects.filter(
            action=AuditAction.RENTAL_STARTED,
            rental_id=rental.pk,
        ).exists()
