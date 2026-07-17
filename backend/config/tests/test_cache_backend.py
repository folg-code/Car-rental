from django.conf import settings
from django.core.cache import cache


def test_pytest_uses_locmem_cache() -> None:
    backend = settings.CACHES["default"]["BACKEND"]
    assert backend.endswith("LocMemCache")
    cache.set("sprint11-cache-probe", "ok", timeout=10)
    assert cache.get("sprint11-cache-probe") == "ok"
