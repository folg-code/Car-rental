import pytest

from apps.fleet.models import Car, CarCategory, CarStatus
from apps.website.selectors.fleet_catalog import get_public_fleet_catalog


@pytest.fixture
def categories(db) -> tuple[CarCategory, CarCategory]:
    compact = CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-public",
        sort_order=1,
    )
    suv = CarCategory.objects.create(
        name="SUV",
        slug="suv-public",
        sort_order=2,
    )
    return compact, suv


@pytest.mark.django_db
class TestPublicFleetCatalogSelector:
    def test_lists_only_active_cars(
        self, categories: tuple[CarCategory, CarCategory]
    ) -> None:
        compact, _suv = categories
        Car.objects.create(
            category=compact,
            registration_number="PUB01",
            make="Toyota",
            model="Yaris",
            year=2022,
            status=CarStatus.ACTIVE,
        )
        Car.objects.create(
            category=compact,
            registration_number="PUB02",
            make="Toyota",
            model="Corolla",
            year=2021,
            status=CarStatus.INACTIVE,
        )

        catalog = get_public_fleet_catalog()

        assert len(catalog.cars) == 1
        assert catalog.cars[0].registration_number == "PUB01"
        assert catalog.categories[0].active_car_count == 1

    def test_filters_by_category_slug(
        self, categories: tuple[CarCategory, CarCategory]
    ) -> None:
        compact, suv = categories
        Car.objects.create(
            category=compact,
            registration_number="PUB03",
            make="Toyota",
            model="Yaris",
            year=2022,
            status=CarStatus.ACTIVE,
        )
        Car.objects.create(
            category=suv,
            registration_number="PUB04",
            make="Skoda",
            model="Kodiaq",
            year=2023,
            status=CarStatus.ACTIVE,
        )

        catalog = get_public_fleet_catalog(category_slug="suv-public")

        assert catalog.selected_category_slug == "suv-public"
        assert len(catalog.cars) == 1
        assert catalog.cars[0].model == "Kodiaq"
