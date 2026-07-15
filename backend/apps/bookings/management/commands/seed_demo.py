from django.core.management.base import BaseCommand

from apps.bookings.demo_seed.builder import DemoSeedBuilder
from apps.bookings.demo_seed.catalog import (
    CARS,
    CUSTOMERS,
    DEMO_CUSTOMER_PASSWORD,
    DEMO_CUSTOMER_USERNAME,
    DEMO_MANAGER_PASSWORD,
    DEMO_MANAGER_USERNAME,
    DEMO_PANEL_PASSWORD,
    DEMO_PANEL_USERNAME,
    SCENARIOS,
)


class Command(BaseCommand):
    help = (
        "Tworzy rozbudowane dane demo: flota, klienci, cennik, rezerwacje "
        "i wynajmy w roznych statusach (idempotentne)."
    )

    def handle(self, *args, **options) -> None:
        self.stdout.write("Seed demo — start")
        summary = DemoSeedBuilder(self.stdout).run()
        self.stdout.write(
            self.style.SUCCESS(
                "Seed demo zakonczony. "
                f"Nowe: {summary.categories} kategorii, {summary.cars} aut, "
                f"{summary.customers} klientow, {summary.reservations} rezerwacji, "
                f"{summary.rentals} wynajmow, {summary.payments} platnosci, "
                f"{summary.invoices} faktur. "
                f"Katalog: {len(CARS)} aut, {len(CUSTOMERS)} klientow, "
                f"{len(SCENARIOS)} scenariuszy. "
                f"Panel: `{DEMO_PANEL_USERNAME}` / `{DEMO_PANEL_PASSWORD}`, "
                f"kierownik: `{DEMO_MANAGER_USERNAME}` / `{DEMO_MANAGER_PASSWORD}`, "
                f"portal: `{DEMO_CUSTOMER_USERNAME}` / `{DEMO_CUSTOMER_PASSWORD}`."
            )
        )
