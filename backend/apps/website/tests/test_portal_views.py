"""Testy portalu klienta — historia rezerwacji i pobieranie dokumentow."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.customer import CustomerService
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.documents.models import Document, DocumentType
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV",
        slug="suv-portal",
        deposit=Decimal("500"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Portal tests",
        slug="portal-tests",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100"),
    )
    return price_list


@pytest.fixture
def customer_user(db):
    return UserService.create_user(
        username="portal-client",
        password="secure-pass-123",
        role=UserRole.CUSTOMER,
    )


@pytest.fixture
def other_customer_user(db):
    return UserService.create_user(
        username="other-client",
        password="secure-pass-123",
        role=UserRole.CUSTOMER,
    )


@pytest.fixture
def customer_profile(customer_user) -> Customer:
    return CustomerService.create(
        user_id=customer_user.pk,
        first_name="Anna",
        last_name="Nowak",
        email="anna@portal.test",
    )


@pytest.fixture
def other_customer_profile(other_customer_user) -> Customer:
    return CustomerService.create(
        user_id=other_customer_user.pk,
        first_name="Jan",
        last_name="Kowalski",
        email="jan@portal.test",
    )


@pytest.fixture
def portal_car(category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="PORTAL01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
    )


@pytest.fixture
def customer_reservation(customer_profile: Customer, portal_car: Car):
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)
    return ReservationService.create(
        customer_id=customer_profile.pk,
        car_id=portal_car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )


@pytest.fixture
def customer_rental(customer_reservation):
    return RentalService.convert_from_reservation(customer_reservation)


@pytest.fixture
def customer_document(customer_rental) -> Document:
    pdf = SimpleUploadedFile(
        "handover.pdf",
        b"%PDF-1.4 portal test",
        content_type="application/pdf",
    )
    return Document.objects.create(
        document_type=DocumentType.RENTAL_CONTRACT_PDF,
        rental=customer_rental,
        customer=customer_rental.reservation.customer,
        file=pdf,
        content_type="application/pdf",
        title="Umowa wynajmu",
    )


@pytest.fixture
def customer_client(customer_user, customer_profile) -> Client:
    client = Client()
    client.force_login(customer_user)
    return client


@pytest.mark.django_db
class TestCustomerPortalViews:
    def test_anonymous_redirects_to_login(self) -> None:
        response = Client().get(reverse("customer_portal:home"))
        assert response.status_code == 302
        assert "logowanie" in response.url

    def test_staff_cannot_access_portal(self, staff_user) -> None:
        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("customer_portal:home"))
        assert response.status_code == 302
        assert "logowanie" in response.url

    def test_customer_without_profile_sees_message(self, customer_user) -> None:
        client = Client()
        client.force_login(customer_user)
        response = client.get(reverse("customer_portal:home"))
        assert response.status_code == 200
        assert b"nie jest jeszcze powiazane" in response.content

    def test_customer_sees_reservations_on_home(
        self,
        customer_client: Client,
        customer_reservation,
    ) -> None:
        response = customer_client.get(reverse("customer_portal:home"))
        assert response.status_code == 200
        assert b"Anna" in response.content
        assert str(customer_reservation.pk).encode() in response.content

    def test_customer_can_list_all_reservations(
        self,
        customer_client: Client,
        customer_reservation,
    ) -> None:
        response = customer_client.get(reverse("customer_portal:reservation_list"))
        assert response.status_code == 200
        assert b"PORTAL01" in response.content

    def test_customer_can_view_own_reservation_detail(
        self,
        customer_client: Client,
        customer_reservation,
    ) -> None:
        url = reverse(
            "customer_portal:reservation_detail",
            kwargs={"reservation_id": customer_reservation.pk},
        )
        response = customer_client.get(url)
        assert response.status_code == 200
        assert b"Toyota" in response.content

    def test_customer_cannot_view_other_reservation(
        self,
        customer_client: Client,
        other_customer_profile: Customer,
        portal_car: Car,
    ) -> None:
        other_reservation = ReservationService.create(
            customer_id=other_customer_profile.pk,
            car_id=portal_car.pk,
            start_at=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
            status=ReservationStatus.CONFIRMED,
        )
        url = reverse(
            "customer_portal:reservation_detail",
            kwargs={"reservation_id": other_reservation.pk},
        )
        response = customer_client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("customer_portal:reservation_list")

    def test_customer_can_download_own_document(
        self,
        customer_client: Client,
        customer_document: Document,
    ) -> None:
        url = reverse(
            "customer_portal:document_download",
            kwargs={"document_uuid": customer_document.uuid},
        )
        response = customer_client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        body = b"".join(response.streaming_content)
        assert body.startswith(b"%PDF")

    def test_customer_cannot_download_other_document(
        self,
        customer_client: Client,
        other_customer_profile: Customer,
        portal_car: Car,
    ) -> None:
        start = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)
        reservation = ReservationService.create(
            customer_id=other_customer_profile.pk,
            car_id=portal_car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        rental = RentalService.convert_from_reservation(reservation)
        pdf = SimpleUploadedFile(
            "other.pdf",
            b"%PDF-1.4 other test",
            content_type="application/pdf",
        )
        document = Document.objects.create(
            document_type=DocumentType.RENTAL_CONTRACT_PDF,
            rental=rental,
            customer=other_customer_profile,
            file=pdf,
            content_type="application/pdf",
        )
        url = reverse(
            "customer_portal:document_download",
            kwargs={"document_uuid": document.uuid},
        )
        response = customer_client.get(url)
        assert response.status_code == 404

    def test_customer_login_redirects_to_portal(self, customer_user) -> None:
        response = Client().post(
            reverse("accounts:login"),
            {"username": "portal-client", "password": "secure-pass-123"},
        )
        assert response.status_code == 302
        assert response.url == reverse("customer_portal:home")


@pytest.fixture
def staff_user(db):
    return UserService.create_user(
        username="portal-staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
