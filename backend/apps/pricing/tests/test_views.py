from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.fleet.models import CarCategory
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="pricing_staff",
        password="secure-pass-123",
        role=UserRole.MANAGER,
    )
    client.login(username="pricing_staff", password="secure-pass-123")
    return client


@pytest.fixture
def price_list(db) -> PriceList:
    return PriceList.objects.create(
        name="Panel test",
        slug="panel-test",
        is_active=True,
    )


@pytest.mark.django_db
class TestPricingPanelViews:
    def test_list_requires_login(self, client) -> None:
        response = client.get(reverse("pricing:price_list_list"))
        assert response.status_code == 302

    def test_list_for_staff(self, staff_client, price_list: PriceList) -> None:
        response = staff_client.get(reverse("pricing:price_list_list"))
        assert response.status_code == 200
        assert b"Panel test" in response.content

    def test_create_price_list(self, staff_client, db) -> None:
        response = staff_client.post(
            reverse("pricing:price_list_create"),
            {
                "name": "Cennik letni",
                "slug": "cennik-letni",
                "description": "",
                "currency": "PLN",
                "valid_from": "",
                "valid_to": "",
                "is_active": "on",
                "is_default": "",
            },
        )
        assert response.status_code == 302
        assert PriceList.objects.filter(slug="cennik-letni").exists()

    def test_add_daily_rate_on_detail(
        self, staff_client, price_list: PriceList, db
    ) -> None:
        category = CarCategory.objects.create(name="Van", slug="van-panel")
        response = staff_client.post(
            reverse("pricing:price_list_detail", kwargs={"pk": price_list.pk}),
            {
                "action": "add_rate",
                "rate-category": category.pk,
                "rate-amount": "150.00",
            },
        )
        assert response.status_code == 302
        assert DailyRate.objects.filter(
            price_list=price_list,
            category=category,
            amount=Decimal("150.00"),
        ).exists()
