import pytest

from apps.notifications.adapters.sms import MockSmsClient, get_sms_client
from apps.notifications.models import SmsStatus
from apps.notifications.services.sms_delivery import SmsDeliveryService


@pytest.fixture(autouse=True)
def sms_settings(settings) -> None:
    settings.SMS_ENABLED = True
    settings.SMS_PROVIDER = "mock"
    settings.SMS_FROM_NUMBER = "+48111111111"


def test_mock_client_returns_external_id() -> None:
    client = MockSmsClient()
    result = client.send_message(
        to="+48111222333",
        body="Test SMS",
        from_number="+48111111111",
    )
    assert result.external_id.startswith("mock_sms_")


def test_get_sms_client_mock(settings) -> None:
    settings.SMS_PROVIDER = "mock"
    client = get_sms_client()
    assert client.provider_name == "mock"


def test_get_sms_client_disabled(settings) -> None:
    settings.SMS_ENABLED = False
    client = get_sms_client()
    assert client.provider_name == "disabled"


@pytest.mark.django_db
def test_delivery_service_creates_log(settings) -> None:
    log = SmsDeliveryService.send(
        "+48111222333",
        "Hello from Car Rental",
    )
    assert log.status == SmsStatus.SENT
    assert log.external_id.startswith("mock_sms_")
