from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.website.adapters.llm import (
    LLMClientError,
    MockLLMClient,
    OpenAICompatibleLLMClient,
    get_llm_client,
)
from apps.website.services.consultant_chat import ConsultantChatService


class TestMockLLMClient:
    def test_responds_to_kaucja_keyword(self) -> None:
        client = MockLLMClient()
        response = client.complete(
            [{"role": "user", "content": "Jak dziala kaucja?"}],
        )
        assert "kaucj" in response.content.lower()

    def test_default_response_mentions_no_booking(self) -> None:
        client = MockLLMClient()
        response = client.complete(
            [{"role": "user", "content": "Czesc"}],
        )
        assert (
            "rezerw" in response.content.lower() or "platn" in response.content.lower()
        )

    def test_get_llm_client_returns_mock_by_default(self) -> None:
        client = get_llm_client()
        assert isinstance(client, MockLLMClient)


class TestOpenAICompatibleLLMClient:
    def _client(self) -> OpenAICompatibleLLMClient:
        return OpenAICompatibleLLMClient(
            api_key="test-key",
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            timeout_seconds=5.0,
            default_max_tokens=256,
        )

    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            OpenAICompatibleLLMClient(
                api_key="  ",
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                timeout_seconds=5.0,
                default_max_tokens=256,
            )

    def test_complete_parses_chat_completion(self) -> None:
        payload = {
            "choices": [
                {"message": {"role": "assistant", "content": "  Hello from model  "}},
            ],
        }
        raw = json.dumps(payload).encode("utf-8")
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = raw
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with patch(
            "apps.website.adapters.llm.urllib.request.urlopen",
            return_value=mock_response,
        ) as urlopen:
            response = self._client().complete(
                [{"role": "user", "content": "Czesc"}],
            )

        assert response.content == "Hello from model"
        request = urlopen.call_args.args[0]
        assert request.full_url == "https://api.openai.com/v1/chat/completions"
        assert request.get_header("Authorization") == "Bearer test-key"
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "gpt-4o-mini"
        assert body["max_tokens"] == 256

    def test_http_error_raises_llm_client_error(self) -> None:
        import urllib.error

        error = urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"error":"bad key"}'),
        )
        with (
            patch(
                "apps.website.adapters.llm.urllib.request.urlopen",
                side_effect=error,
            ),
            pytest.raises(LLMClientError, match="HTTP 401"),
        ):
            self._client().complete([{"role": "user", "content": "Czesc"}])

    def test_empty_choices_raises(self) -> None:
        raw = json.dumps({"choices": []}).encode("utf-8")
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = raw
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        with (
            patch(
                "apps.website.adapters.llm.urllib.request.urlopen",
                return_value=mock_response,
            ),
            pytest.raises(LLMClientError, match="empty content"),
        ):
            self._client().complete([{"role": "user", "content": "Czesc"}])

    @override_settings(
        LLM_PROVIDER="openai",
        LLM_API_KEY="sk-test",
        LLM_MODEL="gpt-4o-mini",
        LLM_BASE_URL="https://example.test/v1",
        LLM_TIMEOUT_SECONDS=12.0,
        LLM_MAX_TOKENS=512,
    )
    def test_factory_returns_openai_client(self) -> None:
        client = get_llm_client()
        assert isinstance(client, OpenAICompatibleLLMClient)
        assert client.provider_name == "openai"

    @override_settings(LLM_PROVIDER="openai", LLM_API_KEY="")
    def test_factory_requires_key_for_openai(self) -> None:
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            get_llm_client()


@pytest.mark.django_db
class TestConsultantChatLlmErrors:
    def test_llm_failure_maps_to_validation_error(self) -> None:
        from apps.website.models import ChatMessage

        class FailingClient:
            def complete(
                self,
                messages: list[dict[str, str]],
                *,
                max_tokens: int | None = None,
            ):
                del messages, max_tokens
                raise LLMClientError("boom")

        with pytest.raises(ValidationError, match="niedostępny"):
            ConsultantChatService.send_message(
                "",
                "Powiedz cos ogolnego bez narzedzi",
                client_ip="127.0.0.1",
                llm_client=FailingClient(),
            )

        assert ChatMessage.objects.count() == 0
