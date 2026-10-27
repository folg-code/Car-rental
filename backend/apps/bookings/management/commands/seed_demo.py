from django.core.management.base import BaseCommand, CommandError

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
from apps.bookings.demo_seed.presentation_check import verify_presentation_seed


class Command(BaseCommand):
    help = (
        "Tworzy rozbudowane dane demo: flota, klienci, cennik, rezerwacje "
        "i wynajmy w roznych statusach (idempotentne). "
        "Na koncu weryfikuje scenariusze sciezki prezentacji."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--check-only",
            action="store_true",
            help="Tylko weryfikacja sciezki prezentacji (bez seedowania).",
        )

    def handle(self, *args, **options) -> None:
        if options["check_only"]:
            self._run_check()
            return

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
        self._run_check()

    def _run_check(self) -> None:
        result = verify_presentation_seed()
        if result.ok:
            self.stdout.write(
                self.style.SUCCESS("OK presentation seed check (sciezka prezentacji).")
            )
            return
        for error in result.errors:
            self.stdout.write(self.style.ERROR(f"  - {error}"))
        raise CommandError(
            "Presentation seed check failed — uruchom seed_demo lub "
            "sprawdz dane (ops-handover-today / ops-return-surcharges / ops-active)."
        )
