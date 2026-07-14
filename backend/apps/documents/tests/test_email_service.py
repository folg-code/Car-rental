from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core import mail
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.models import Document, DocumentType, EmailStatus
from apps.documents.services.email import EmailService
from apps.documents.tests.conftest import tiny_signature_image
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.operations.services.handover import HandoverService
from apps.operations.services.return_workflow import ReturnService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV", slug="suv-email", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def locmem_email(settings) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@test.car-rental.local"


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Email test",
        slug="email-test",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("100"))
    return pl


@pytest.fixture
def scheduled_rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Anna",
        last_name="Nowak",
        email="anna@email.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1MAIL01",
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
def handover_document(scheduled_rental) -> Document:
    HandoverService.complete_handover(
        scheduled_rental.pk,
        mileage=10_200,
        fuel_level_percent=90,
        signer_name="Anna Nowak",
        signature_image=tiny_signature_image(),
    )
    return Document.objects.get(
        handover_protocol__rental=scheduled_rental,
        document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
        version=1,
    )


@pytest.mark.django_db
class TestEmailService:
    def test_send_document_email_success(self, handover_document: Document) -> None:
        mail.outbox.clear()
        log = EmailService.send_document_email(
            handover_document.pk,
            force_resend=True,
        )
        assert log is not None
        assert log.status == EmailStatus.SENT
        assert log.sent_at is not None
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["anna@email.test"]
        assert "wydania" in mail.outbox[0].subject.lower()
        assert len(mail.outbox[0].attachments) == 1
        assert mail.outbox[0].attachments[0][2] == "application/pdf"

    def test_skips_resend_without_force(self, handover_document: Document) -> None:
        first = EmailService.send_document_email(
            handover_document.pk,
            force_resend=True,
        )
        mail.outbox.clear()
        second = EmailService.send_document_email(handover_document.pk)
        assert second is not None
        assert second.pk == first.pk
        assert len(mail.outbox) == 0

    def test_missing_customer_email_fails_log(
        self,
        handover_document: Document,
    ) -> None:
        Customer.objects.filter(pk=handover_document.customer_id).update(
            email="",
            phone="",
        )
        handover_document.customer.refresh_from_db()

        log = EmailService.send_document_email(
            handover_document.pk,
            force_resend=True,
        )
        assert log is not None
        assert log.status == EmailStatus.FAILED
        assert "email" in log.error_message.lower()

    def test_retry_failed_email(self, handover_document: Document) -> None:
        Customer.objects.filter(pk=handover_document.customer_id).update(
            email="",
            phone="",
        )
        handover_document.customer.refresh_from_db()
        failed = EmailService.send_document_email(
            handover_document.pk,
            force_resend=True,
        )
        assert failed is not None
        assert failed.status == EmailStatus.FAILED

        Customer.objects.filter(pk=handover_document.customer_id).update(
            email="anna@email.test",
            phone="500600700",
        )
        handover_document.customer.refresh_from_db()
        mail.outbox.clear()

        retried = EmailService.retry_email(failed.pk)
        assert retried is not None
        assert retried.status == EmailStatus.SENT
        assert len(mail.outbox) == 1

    def test_retry_rejects_non_failed_log(self, handover_document: Document) -> None:
        sent = EmailService.send_document_email(
            handover_document.pk,
            force_resend=True,
        )
        assert sent is not None
        with pytest.raises(ValidationError, match="failed"):
            EmailService.retry_email(sent.pk)


@pytest.mark.django_db
class TestEmailIntegrationWithDocumentService:
    def test_complete_handover_sends_email_via_document_service(
        self,
        scheduled_rental,
    ) -> None:
        mail.outbox.clear()
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_200,
            fuel_level_percent=90,
            signer_name="Anna Nowak",
            signature_image=tiny_signature_image(),
        )
        doc = Document.objects.get(
            document_type=DocumentType.HANDOVER_PROTOCOL_PDF,
            rental=scheduled_rental,
            version=1,
        )
        log = doc.email_logs.filter(status=EmailStatus.SENT).first()
        assert log is not None
        assert len(mail.outbox) == 1

    def test_complete_return_sends_email(self, scheduled_rental) -> None:
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Anna",
            signature_image=tiny_signature_image(),
        )
        mail.outbox.clear()
        ReturnService.complete_return(
            scheduled_rental.pk,
            mileage=10_300,
            fuel_level_percent=80,
            signer_name="Anna",
            signature_image=tiny_signature_image("ret.png"),
        )
        doc = Document.objects.get(
            document_type=DocumentType.RETURN_PROTOCOL_PDF,
            rental=scheduled_rental,
            version=1,
        )
        assert doc.email_logs.filter(status=EmailStatus.SENT).exists()
        assert len(mail.outbox) == 1
        assert "zwrotu" in mail.outbox[0].subject.lower()
