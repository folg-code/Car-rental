from decimal import Decimal

import pytest
from django.template import Context, Template


@pytest.mark.django_db
def test_damage_marker_style_uses_dot_decimal_not_locale_comma() -> None:
    """Locale pl formats Decimal as 40,50 — CSS needs 40.50."""

    class Marker:
        pos_x = Decimal("40.50")
        pos_y = Decimal("12.25")

    html = Template(
        '{% load l10n %}{% include "operations/_damage_marker_style.html" %}'
    ).render(Context({"marker": Marker()}))

    assert "40.50" in html
    assert "12.25" in html
    assert "40,50" not in html
    assert "12,25" not in html


def test_parse_diagram_percent_accepts_comma() -> None:
    from apps.operations.views import _parse_diagram_percent

    assert _parse_diagram_percent("33,5") == Decimal("33.5")
    assert _parse_diagram_percent("") == Decimal("50")
