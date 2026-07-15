from django.conf import settings


def site_flags(request) -> dict[str, bool]:
    return {"demo_site": getattr(settings, "DEMO_SITE", False)}
