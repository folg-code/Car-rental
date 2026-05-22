from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.fleet.models import Car, CarCategory


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="fleet_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="fleet_staff", password="secure-pass-123")
    return client


@pytest.fixture
def sample_car(db) -> Car:
    cat = CarCategory.objects.create(name="SUV", slug="suv")
    return Car.objects.create(
        category=cat,
        registration_number="KR1A1111",
        make="Skoda",
        model="Kodiaq",
        year=2023,
    )


@pytest.mark.django_db
class TestFleetViews:
    def test_car_list_requires_login(self, client) -> None:
        response = client.get(reverse("fleet:car_list"))
        assert response.status_code == 302

    def test_car_list_for_staff(self, staff_client, sample_car: Car) -> None:
        response = staff_client.get(reverse("fleet:car_list"))
        assert response.status_code == 200
        assert sample_car.registration_number.encode() in response.content

    def test_car_create(self, staff_client, db) -> None:
        CarCategory.objects.create(name="Ekonomiczna", slug="ekonomiczna")
        response = staff_client.post(
            reverse("fleet:car_create"),
            {
                "category": CarCategory.objects.get(slug="ekonomiczna").pk,
                "registration_number": "GD99999",
                "make": "Fiat",
                "model": "500",
                "year": 2021,
                "status": "active",
                "fuel_type": "petrol",
                "mileage": 45000,
                "seats": 4,
                "notes": "",
                "vin": "",
                "color": "czerwony",
            },
        )
        assert response.status_code == 302
        assert Car.objects.filter(registration_number="GD99999").exists()

    def test_category_edit_updates_deposit(self, staff_client, db) -> None:
        category = CarCategory.objects.create(
            name="Premium",
            slug="premium",
            deposit=Decimal("1000.00"),
        )
        response = staff_client.post(
            reverse("fleet:category_edit", kwargs={"pk": category.pk}),
            {
                "name": "Premium Plus",
                "slug": "premium",
                "description": "",
                "sort_order": 0,
                "deposit": "2500.50",
            },
        )
        assert response.status_code == 302
        category.refresh_from_db()
        assert category.name == "Premium Plus"
        assert category.deposit == Decimal("2500.50")
