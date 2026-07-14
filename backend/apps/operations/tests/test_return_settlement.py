from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.bookings.models import RentalStatus
from apps.operations.services.handover import HandoverService
from apps.operations.services.return_workflow import ReturnService
from apps.payments.models import PaymentMethod, PaymentType
from apps.payments.selectors.payment import (
    get_rental_balance_due,
    get_rental_payment_summary,
)
from apps.payments.services.payment import PaymentService
from apps.payments.services.settlement import SettlementService


def _tiny_image(name: str = "sig.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        b"\x89PNG\r\n\x1a\n",
        content_type="image/png",
    )


@pytest.mark.django_db
class TestReturnSurchargeSettlement:
    def test_auto_close_after_all_charges_paid(self, scheduled_rental) -> None:
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )
        scheduled_rental.refresh_from_db()

        ReturnService.complete_return(
            scheduled_rental.pk,
            mileage=10_350,
            fuel_level_percent=70,
            signer_name="Jan",
            signature_image=_tiny_image("ret.png"),
        )
        scheduled_rental.refresh_from_db()
        assert scheduled_rental.status == RentalStatus.RETURNED
        assert get_rental_balance_due(scheduled_rental.pk) > Decimal("0")

        summary = get_rental_payment_summary(scheduled_rental.pk)
        if summary["rental_fee_due"] > 0:
            PaymentService.record_rental_fee(
                rental_id=scheduled_rental.pk,
                amount=summary["rental_fee_due"],
                method=PaymentMethod.CASH,
            )
        if summary["extra_charges_due"] > 0:
            PaymentService.record_payment(
                rental_id=scheduled_rental.pk,
                amount=summary["extra_charges_due"],
                payment_type=PaymentType.EXTRA_CHARGE,
                method=PaymentMethod.CASH,
            )

        scheduled_rental.refresh_from_db()
        assert scheduled_rental.status == RentalStatus.CLOSED
        assert get_rental_balance_due(scheduled_rental.pk) == Decimal("0")

    def test_try_close_does_not_close_with_outstanding_due(
        self, scheduled_rental
    ) -> None:
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )
        ReturnService.complete_return(
            scheduled_rental.pk,
            mileage=10_350,
            fuel_level_percent=70,
            signer_name="Jan",
            signature_image=_tiny_image("ret2.png"),
        )
        scheduled_rental.refresh_from_db()
        assert (
            SettlementService.try_close_rental_if_settled(scheduled_rental.pk) is False
        )
        scheduled_rental.refresh_from_db()
        assert scheduled_rental.status == RentalStatus.RETURNED
