import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestWebsiteLanding:
    def test_landing_returns_200(self, client) -> None:
        response = client.get(reverse("website:home"))
        assert response.status_code == 200

    def test_landing_uses_public_layout(self, client) -> None:
        response = client.get(reverse("website:home"))
        content = response.content
        assert b"Zarezerwuj auto szybko i wygodnie" in content
        assert "Jak to działa".encode() in content
        assert b"Panel operacyjny" not in content

    def test_root_url_resolves_to_website(self, client) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert b"Car Rental" in response.content
