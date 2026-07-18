from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.dashboard.selectors.financial_reports import get_financial_period_report
from apps.documents.models import InvoiceStatus
from apps.documents.services.invoice import InvoiceService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.models import PaymentMethod, PaymentType, RentalCharge
from apps.payments.services.payment import PaymentService


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="reports_staff",
        password="secure-pass-123",
        role=UserRole.MANAGER,
    )
    client.login(username="reports_staff", password="secure-pass-123")
    return client


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-reports",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory):
    from apps.pricing.models import DailyRate, PriceList

    price_list = PriceList.objects.create(
        name="Cennik reports",
        slug="test-reports",
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
        first_name="Jan",
        last_name="Kowalski",
        email="jan@reports.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1REP01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )
    start = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 7, 5, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)


@pytest.mark.django_db
class TestFinancialPeriodReport:
    def test_report_separates_revenue_deposits_and_invoices(self, rental) -> None:
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("500.00"),
            paid_at=datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
        )
        PaymentService.record_deposit(
            rental_id=rental.pk,
            paid_at=datetime(2026, 7, 10, 10, 0, tzinfo=UTC),
        )
        PaymentService.record_payment(
            rental_id=rental.pk,
            amount=Decimal("50.00"),
            payment_type=PaymentType.EXTRA_CHARGE,
            method=PaymentMethod.CASH,
            paid_at=datetime(2026, 7, 12, 14, 0, tzinfo=UTC),
        )
        PaymentService.refund_deposit(
            rental_id=rental.pk,
            amount=Decimal("100.00"),
            paid_at=datetime(2026, 7, 13, 11, 0, tzinfo=UTC),
        )
        RentalCharge.objects.create(
            rental=rental,
            idempotency_key="report-charge-1",
            payment_type=PaymentType.EXTRA_CHARGE,
            source_code="fuel",
            description="Paliwo",
            amount=Decimal("75.00"),
        )
        invoice = InvoiceService.create_from_rental(
            rental.pk,
            issue_date=date(2026, 7, 15),
        )
        InvoiceService.issue(invoice.pk)

        report = get_financial_period_report(
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )

        assert report.revenue_total == Decimal("550.00")
        assert report.revenue.rental_fees == Decimal("500.00")
        assert report.revenue.extra_charges == Decimal("50.00")
        assert report.deposits_collected == Decimal("1000.00")
        assert report.refunds_paid == Decimal("100.00")
        assert report.deposit_net == Decimal("900.00")
        assert report.charges_accrued == Decimal("75.00")
        assert report.invoice_total == invoice.total_amount
        assert report.invoice_count == 1

    def test_report_excludes_cancelled_invoices(self, rental) -> None:
        invoice = InvoiceService.create_from_rental(
            rental.pk,
            issue_date=date(2026, 7, 5),
        )
        InvoiceService.issue(invoice.pk)
        invoice.status = InvoiceStatus.CANCELLED
        invoice.save(update_fields=["status"])

        report = get_financial_period_report(
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )

        assert report.invoice_count == 0
        assert report.invoice_total == Decimal("0")

    def test_report_excludes_payments_outside_period(self, rental) -> None:
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("300.00"),
            paid_at=datetime(2026, 6, 15, 10, 0, tzinfo=UTC),
        )
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("200.00"),
            paid_at=datetime(2026, 7, 15, 10, 0, tzinfo=UTC),
        )

        report = get_financial_period_report(
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )

        assert report.revenue_total == Decimal("200.00")


@pytest.mark.django_db
class TestFinancialReportView:
    def test_requires_login(self, client) -> None:
        response = client.get(reverse("dashboard:financial_report"))
        assert response.status_code == 302

    def test_renders_report_for_staff(self, staff_client, rental) -> None:
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("400.00"),
            paid_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
        response = staff_client.get(
            reverse("dashboard:financial_report"),
            {"from": "2026-07-01", "to": "2026-07-31"},
        )

        assert response.status_code == 200
        assert b"Raport finansowy" in response.content
        assert b"Przychod operacyjny" in response.content
        assert response.context["report"].revenue_total == Decimal("400.00")
