from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.consultant_chat import ConsultantChatService


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-chat-tools")


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Test chat tools",
        slug="test-chat-tools",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100.00"),
    )
    return price_list


@pytest.fixture
def car(db, category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="CHAT01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestConsultantChatToolsIntegration:
    def test_availability_message_uses_tools_not_llm(self, car: Car) -> None:
        del car
        assistant = ConsultantChatService.send_message(
            "",
            "Jakie auta sa wolne 2026-09-10 i 2026-09-15?",
            client_ip="127.0.0.1",
        )
        assert "Toyota" in assistant.content
        assert reverse("website:car_offer") in assistant.content

    def test_customer_sees_reservation_status(
        self,
        car: Car,
        django_user_model,
    ) -> None:
        user = django_user_model.objects.create_user(
            username="client1",
            password="test-pass-123",
            role=UserRole.CUSTOMER,
        )
        customer = Customer.objects.create(
            user=user,
            first_name="Jan",
            last_name="Klient",
            email="jan@client.test",
        )
        ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
            status=ReservationStatus.CONFIRMED,
        )
        assistant = ConsultantChatService.send_message(
            "session-1",
            "Jaki status mojej rezerwacji?",
            client_ip="127.0.0.1",
            user=user,
        )
        assert "Potwierdzona" in assistant.content

    def test_clarifying_question_without_dates(self) -> None:
        assistant = ConsultantChatService.send_message(
            "",
            "Sprawdz dostepnosc samochodow",
            client_ip="127.0.0.1",
        )
        assert "termin" in assistant.content.lower()

    def test_deposit_question(self, category: CarCategory) -> None:
        category.deposit = Decimal("1800.00")
        category.save(update_fields=["deposit"])
        assistant = ConsultantChatService.send_message(
            "",
            "Jaka kaucja za kompakt?",
            client_ip="127.0.0.1",
        )
        assert "1800.00" in assistant.content
        assert "kaucj" in assistant.content.lower()
