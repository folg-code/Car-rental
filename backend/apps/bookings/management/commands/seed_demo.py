from django.core.management.base import BaseCommand

from apps.bookings.demo_seed.builder import DemoSeedBuilder
from apps.bookings.demo_seed.catalog import CARS, CUSTOMERS, SCENARIOS


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
                f"{summary.rentals} wynajmow. "
                f"Katalog: {len(CARS)} aut, {len(CUSTOMERS)} klientow, "
                f"{len(SCENARIOS)} scenariuszy."
            )
        )
