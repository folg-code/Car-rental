from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from apps.payments.models import PaymentType, RentalCharge


@dataclass(frozen=True)
class AccruedChargeLine:
    source_code: str
    description: str
    amount: Decimal
    payment_type: str = PaymentType.EXTRA_CHARGE


class RentalChargeService:
    @staticmethod
    def _idempotency_key(
        rental_id: int,
        return_protocol_id: int | None,
        source_code: str,
    ) -> str:
        if return_protocol_id is not None:
            return f"return:{return_protocol_id}:{source_code}"
        return f"rental:{rental_id}:{source_code}"

    @staticmethod
    @transaction.atomic
    def accrue_return_surcharges(
        *,
        rental_id: int,
        return_protocol_id: int | None,
        lines: tuple[AccruedChargeLine, ...],
    ) -> list[RentalCharge]:
        created: list[RentalCharge] = []
        for line in lines:
            if line.amount <= 0:
                continue
            key = RentalChargeService._idempotency_key(
                rental_id,
                return_protocol_id,
                line.source_code,
            )
            charge, was_created = RentalCharge.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    "rental_id": rental_id,
                    "return_protocol_id": return_protocol_id,
                    "payment_type": line.payment_type,
                    "source_code": line.source_code,
                    "description": line.description,
                    "amount": line.amount.quantize(Decimal("0.01")),
                },
            )
            if was_created:
                created.append(charge)
        return created
