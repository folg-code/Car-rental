import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse


@pytest.mark.django_db
class TestConsultantViews:
    def setup_method(self) -> None:
        cache.clear()

    def test_consultant_page_returns_200(self, client) -> None:
        response = client.get(reverse("website:consultant"))
        assert response.status_code == 200
        assert "Asystent wypożyczalni".encode() in response.content
        assert b"PESEL" in response.content
        assert b"Wolne auta na jutro" in response.content
        assert "Czy są wolne auta na jutro?".encode() in response.content

    def test_consultant_sets_session_cookie(self, client) -> None:
        response = client.get(reverse("website:consultant"))
        assert "chat_session_id" in response.cookies

    def test_post_message_returns_assistant_reply(self, client) -> None:
        client.get(reverse("website:consultant"))
        response = client.post(
            reverse("website:consultant_message"),
            {"message": "Jak dziala kaucja?"},
        )
        assert response.status_code == 302
        follow = client.get(reverse("website:consultant"))
        assert b"kaucj" in follow.content.lower()

    def test_htmx_post_appends_message_pair(self, client) -> None:
        client.get(reverse("website:consultant"))
        response = client.post(
            reverse("website:consultant_message"),
            {"message": "Jak zarezerwowac?"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"rezerw" in response.content.lower()

    def test_widget_link_on_public_pages(self, client) -> None:
        response = client.get(reverse("website:home"))
        assert b"Pomoc" in response.content
        assert b"chat z asystentem" in response.content.lower()

    @override_settings(CHAT_RATE_LIMIT_PER_HOUR=1)
    def test_rate_limit_returns_400_on_htmx(self, client) -> None:
        client.get(reverse("website:consultant"))
        client.post(
            reverse("website:consultant_message"),
            {"message": "Pierwsze"},
            HTTP_HX_REQUEST="true",
        )
        response = client.post(
            reverse("website:consultant_message"),
            {"message": "Drugie"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 400
        assert b"limit" in response.content.lower()

    def test_get_message_endpoint_not_allowed(self, client) -> None:
        response = client.get(reverse("website:consultant_message"))
        assert response.status_code == 405
