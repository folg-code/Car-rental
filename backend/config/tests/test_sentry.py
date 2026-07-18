from unittest.mock import patch

from config.sentry import init_sentry


def test_init_sentry_noop_without_dsn() -> None:
    with patch("sentry_sdk.init") as mock_init:
        assert init_sentry(dsn="", environment="test") is False
        mock_init.assert_not_called()


def test_init_sentry_calls_sdk_with_dsn() -> None:
    with patch("sentry_sdk.init") as mock_init:
        assert (
            init_sentry(
                dsn="https://key@example.com/1",
                environment="test",
                release="abc123",
                traces_sample_rate=0.1,
                send_default_pii=False,
            )
            is True
        )
        mock_init.assert_called_once()
        kwargs = mock_init.call_args.kwargs
        assert kwargs["dsn"] == "https://key@example.com/1"
        assert kwargs["environment"] == "test"
        assert kwargs["release"] == "abc123"
        assert kwargs["traces_sample_rate"] == 0.1
        assert kwargs["send_default_pii"] is False
        assert len(kwargs["integrations"]) == 4


def test_settings_expose_sentry_defaults(settings) -> None:
    assert settings.SENTRY_DSN == ""
    assert settings.SENTRY_SEND_DEFAULT_PII is False
    assert settings.SENTRY_TRACES_SAMPLE_RATE == 0.0
