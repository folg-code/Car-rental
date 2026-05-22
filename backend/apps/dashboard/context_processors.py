from apps.dashboard.navigation import PANEL_NAVIGATION


def panel_navigation(request):
    match = request.resolver_match
    if match and match.app_name == "fleet":
        panel_section = "fleet"
    elif match and match.app_name == "bookings":
        panel_section = "bookings"
    elif match:
        panel_section = match.url_name
    else:
        panel_section = None

    return {
        "panel_navigation": PANEL_NAVIGATION,
        "panel_section": panel_section,
    }
