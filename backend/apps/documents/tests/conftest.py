import pytest

pytest_plugins = ["apps.operations.tests.conftest"]


@pytest.fixture(autouse=True)
def locmem_email(settings) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@test.car-rental.local"
