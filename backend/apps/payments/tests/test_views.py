from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.payments.models import PaymentMethod, PaymentType
from apps.payments.services.payment import PaymentService


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="pay_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="pay_staff", password="secure-pass-123")
    return client


@pytest.mark.django_db
class TestPaymentViews:
    def test_payment_list_requires_login(self, client) -> None:
        response = client.get(reverse("payments:payment_list"))
        assert response.status_code == 302

    def test_payment_list_for_staff(self, staff_client, rental) -> None:
        response = staff_client.get(reverse("payments:payment_list"))
        assert response.status_code == 200

    def test_payment_list_handles_reservation_only_payment(
        self, staff_client, reservation
    ) -> None:
        PaymentService.record_reservation_payment(
            reservation_id=reservation.pk,
            amount=Decimal("800.00"),
            payment_type=PaymentType.RENTAL_FEE,
            method=PaymentMethod.ONLINE_GATEWAY,
        )
        response = staff_client.get(reverse("payments:payment_list"))
        assert response.status_code == 200
        assert b"Rezerwacja #" in response.content
        assert reservation.customer.full_name.encode() in response.content

    def test_rental_payments_page(self, staff_client, rental) -> None:
        response = staff_client.get(
            reverse("payments:rental_payments", kwargs={"rental_id": rental.pk})
        )
        assert response.status_code == 200
        assert "Do zapłaty".encode() in response.content

    def test_record_deposit_quick_updates_summary(self, staff_client, rental) -> None:
        url = reverse("payments:rental_payments", kwargs={"rental_id": rental.pk})
        quick_url = reverse(
            "payments:record_deposit_quick",
            kwargs={"rental_id": rental.pk},
        )
        before = staff_client.get(url)
        assert before.status_code == 200
        assert b"0,00 PLN" in before.content or b"0.00 PLN" in before.content

        response = staff_client.post(quick_url)
        assert response.status_code == 302
        assert response.url == url

        after = staff_client.get(url)
        assert after.status_code == 200
        assert str(rental.deposit_amount).encode() in after.content

    def test_record_payment_form_updates_summary(self, staff_client, rental) -> None:
        from apps.bookings.services.price_snapshot import PriceSnapshotService

        due = PriceSnapshotService.reservation_total(rental.reservation)
        url = reverse("payments:rental_payments", kwargs={"rental_id": rental.pk})
        response = staff_client.post(
            url,
            {
                "payment_type": PaymentType.RENTAL_FEE,
                "method": PaymentMethod.CASH,
                "amount": str(due),
                "paid_at": "2026-07-10T10:00",
                "notes": "",
            },
        )
        assert response.status_code == 302

        page = staff_client.get(url)
        assert page.status_code == 200
        assert b"0,00 PLN" in page.content or b"0.00 PLN" in page.content
        from apps.payments.selectors.payment import get_rental_payment_summary

        summary = get_rental_payment_summary(rental.pk)
        assert summary["rental_fees_paid"] == due
        assert summary["revenue_total"] == due
