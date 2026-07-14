from __future__ import annotations

from apps.bookings.models import Rental, RentalStatus
from apps.bookings.services.rental import RentalService
from apps.payments.selectors.payment import get_rental_balance_due


class SettlementService:
    @staticmethod
    def try_close_rental_if_settled(rental_id: int) -> bool:
        rental = Rental.objects.filter(pk=rental_id).first()
        if rental is None or rental.status != RentalStatus.RETURNED:
            return False
        if get_rental_balance_due(rental_id) > 0:
            return False
        RentalService.close(rental)
        return True
