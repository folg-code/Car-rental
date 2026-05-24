from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PanelNavItem:
    label: str
    url_name: str | None
    section_key: str
    icon: str = ""
    enabled: bool = True


PANEL_NAVIGATION: tuple[PanelNavItem, ...] = (
    PanelNavItem(
        label="Pulpit", url_name="dashboard:home", section_key="home", icon="home"
    ),
    PanelNavItem(
        label="Flota",
        url_name="fleet:car_list",
        section_key="fleet",
        icon="car",
        enabled=True,
    ),
    PanelNavItem(
        label="Rezerwacje",
        url_name="bookings:reservation_list",
        section_key="bookings",
        icon="calendar",
        enabled=True,
    ),
    PanelNavItem(
        label="Cenniki",
        url_name="pricing:price_list_list",
        section_key="pricing",
        icon="tag",
        enabled=True,
    ),
    PanelNavItem(
        label="Operacje",
        url_name="operations:home",
        section_key="operations",
        icon="clipboard",
        enabled=True,
    ),
    PanelNavItem(
        label="Platnosci",
        url_name="payments:payment_list",
        section_key="payments",
        icon="wallet",
        enabled=True,
    ),
    PanelNavItem(
        label="Dokumenty",
        url_name="documents:home",
        section_key="documents",
        icon="file",
        enabled=True,
    ),
)
