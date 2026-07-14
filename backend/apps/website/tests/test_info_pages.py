import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestInfoPages:
    def test_terms_returns_placeholder(self, client) -> None:
        response = client.get(reverse("website:terms"))
        assert response.status_code == 200
        assert b"Regulamin wypozyczalni" in response.content
        assert b"Placeholder" in response.content

    def test_contact_returns_placeholder(self, client) -> None:
        response = client.get(reverse("website:contact"))
        assert response.status_code == 200
        assert b"miejsce na dane kontaktowe" in response.content.lower()
        assert b"Miejsce na adres" in response.content

    def test_faq_returns_sample_questions(self, client) -> None:
        response = client.get(reverse("website:faq"))
        assert response.status_code == 200
        assert b"Czesto zadawane pytania" in response.content
        assert b"Jak zarezerwowac auto online" in response.content

    def test_nav_links_to_info_pages(self, client) -> None:
        response = client.get(reverse("website:home"))
        content = response.content.decode()
        assert reverse("website:terms") in content
        assert reverse("website:contact") in content
        assert reverse("website:faq") in content
