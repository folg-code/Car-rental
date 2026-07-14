from apps.website.adapters.llm import MockLLMClient, get_llm_client


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
