import pytest
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.accounts.services.user import UserService
from apps.website.models import ChatMessage, ChatMessageRole, ChatSession


@pytest.fixture
def staff_user(db):
    return UserService.create_user(
        username="support-staff",
        password="secure-pass-123",
        role=UserRole.MANAGER,
    )


@pytest.fixture
def chat_session(db) -> ChatSession:
    session = ChatSession.objects.create(session_key="support-test-key")
    ChatMessage.objects.create(
        session=session,
        role=ChatMessageRole.USER,
        content="Pytanie o kaucje",
    )
    ChatMessage.objects.create(
        session=session,
        role=ChatMessageRole.ASSISTANT,
        content="Kaucja jest zwrotna po wynajmie.",
    )
    return session


@pytest.mark.django_db
class TestChatSupportPanel:
    def test_anonymous_redirects_to_login(self, client) -> None:
        response = client.get(reverse("website_support:session_list"))
        assert response.status_code == 302
        assert "konto" in response.url

    def test_staff_can_list_sessions(
        self,
        client,
        staff_user,
        chat_session: ChatSession,
    ) -> None:
        del staff_user
        client.login(username="support-staff", password="secure-pass-123")
        response = client.get(reverse("website_support:session_list"))
        assert response.status_code == 200
        assert b"support-test-key" not in response.content
        assert str(chat_session.pk).encode() in response.content

    def test_staff_can_view_session_detail(
        self,
        client,
        staff_user,
        chat_session: ChatSession,
    ) -> None:
        del staff_user
        client.login(username="support-staff", password="secure-pass-123")
        response = client.get(
            reverse(
                "website_support:session_detail",
                kwargs={"session_id": chat_session.pk},
            ),
        )
        assert response.status_code == 200
        assert b"kaucj" in response.content.lower()

    def test_unknown_session_redirects_to_list(self, client, staff_user) -> None:
        del staff_user
        client.login(username="support-staff", password="secure-pass-123")
        response = client.get(
            reverse("website_support:session_detail", kwargs={"session_id": 99999}),
        )
        assert response.status_code == 302
        assert response.url == reverse("website_support:session_list")
