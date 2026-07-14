from django.conf import settings


def test_email_settings_defaults() -> None:
    assert settings.EMAIL_BACKEND.endswith("EmailBackend")
    assert settings.EMAIL_HOST == "localhost"
    assert settings.EMAIL_PORT == 587
    assert settings.EMAIL_USE_TLS is True
    assert settings.EMAIL_USE_SSL is False
    assert settings.EMAIL_TIMEOUT == 10
