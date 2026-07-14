import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.operations.services.handover import HandoverService
from apps.operations.tests.test_operations import _tiny_image


@pytest.fixture
def staff_client(client, db):
    UserService.create_user(
        username="ops_staff",
        password="secure-pass-123",
        role=UserRole.EMPLOYEE,
    )
    client.login(username="ops_staff", password="secure-pass-123")
    return client


@pytest.mark.django_db
class TestOperationsViews:
    def test_home_requires_login(self, client) -> None:
        assert client.get(reverse("operations:home")).status_code == 302

    def test_home_for_staff(self, staff_client, scheduled_rental) -> None:
        response = staff_client.get(reverse("operations:home"))
        assert response.status_code == 200
        assert b"Operacje w terenie" in response.content

    def test_handover_form_has_wizard(self, staff_client, scheduled_rental) -> None:
        response = staff_client.get(
            reverse(
                "operations:handover_create",
                kwargs={"rental_id": scheduled_rental.pk},
            )
        )
        assert response.status_code == 200
        assert b"Protokol wydania" in response.content
        assert b"op-wizard-nav" in response.content
        assert b"Krok 1: Dane pojazdu" in response.content

    def test_return_form_has_wizard_and_htmx_preview(
        self, staff_client, scheduled_rental
    ) -> None:
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )
        response = staff_client.get(
            reverse(
                "operations:return_create",
                kwargs={"rental_id": scheduled_rental.pk},
            )
        )
        assert response.status_code == 200
        assert b"Protokol zwrotu" in response.content
        assert b"op-wizard-nav" in response.content
        assert b"Krok 1: Stan przy zwrocie" in response.content
        assert b"Podglad doplat" in response.content
        assert b"hx-get" in response.content
        assert b"Porownanie szkod" in response.content

    def test_return_surcharge_preview_endpoint(
        self, staff_client, scheduled_rental
    ) -> None:
        HandoverService.complete_handover(
            scheduled_rental.pk,
            mileage=10_000,
            fuel_level_percent=100,
            signer_name="Jan",
            signature_image=_tiny_image(),
        )
        url = reverse(
            "operations:return_surcharge_preview",
            kwargs={"rental_id": scheduled_rental.pk},
        )
        response = staff_client.get(url, {"mileage": 10350, "fuel_level_percent": 70})
        assert response.status_code == 200
        assert b"Przejechane km" in response.content or b"km" in response.content
