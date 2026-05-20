from apps.dashboard.navigation import PANEL_NAVIGATION


def panel_navigation(request):
    return {
        "panel_navigation": PANEL_NAVIGATION,
        "panel_section": getattr(request.resolver_match, "url_name", None)
        if request.resolver_match
        else None,
    }
