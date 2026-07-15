import pytest
from django.urls import reverse

from apps.fleet.models import Car, CarCategory, CarStatus


@pytest.fixture
def public_car(db) -> Car:
    category = CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-fleet-ui",
    )
    return Car.objects.create(
        category=category,
        registration_number="FLEET01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestPublicFleetListView:
    def test_fleet_list_returns_200(self, client) -> None:
        response = client.get(reverse("website:fleet_list"))
        assert response.status_code == 200
        assert b"Nasza flota" in response.content

    def test_fleet_list_shows_active_car(self, client, public_car: Car) -> None:
        response = client.get(reverse("website:fleet_list"))
        assert response.status_code == 200
        assert b"Toyota" in response.content
        assert b"Yaris" in response.content
        assert b"FLEET01" not in response.content

    def test_fleet_list_filters_by_category(self, client, public_car: Car) -> None:
        url = reverse("website:fleet_list")
        response = client.get(f"{url}?kategoria=kompakt-fleet-ui")
        assert response.status_code == 200
        assert b"Yaris" in response.content

        response_other = client.get(f"{url}?kategoria=nieistniejaca")
        assert response_other.status_code == 200
        assert "Brak pojazdów".encode() in response_other.content
