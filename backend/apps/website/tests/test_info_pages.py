import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestInfoPages:
    def test_terms_returns_placeholder(self, client) -> None:
        response = client.get(reverse("website:terms"))
        assert response.status_code == 200
        assert "Regulamin wypożyczalni".encode() in response.content
        assert "Postanowienia ogólne".encode() in response.content

    def test_contact_returns_placeholder(self, client) -> None:
        response = client.get(reverse("website:contact"))
        assert response.status_code == 200
        assert b"Kontakt" in response.content
        assert b"kontakt@car-rental.local" in response.content

    def test_faq_returns_sample_questions(self, client) -> None:
        response = client.get(reverse("website:faq"))
        assert response.status_code == 200
        assert "Często zadawane pytania".encode() in response.content
        assert "Jak zarezerwować auto online".encode() in response.content

    def test_nav_links_to_info_pages(self, client) -> None:
        response = client.get(reverse("website:home"))
        content = response.content.decode()
        assert reverse("website:terms") in content
        assert reverse("website:contact") in content
        assert reverse("website:faq") in content
