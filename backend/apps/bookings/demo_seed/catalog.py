from dataclasses import dataclass
from decimal import Decimal

from apps.bookings.models import ReservationStatus
from apps.fleet.models import CarStatus, FuelType

DEMO_SEED_PREFIX = "DEMO_SEED:"


def demo_note(key: str) -> str:
    return f"{DEMO_SEED_PREFIX}{key}"


@dataclass(frozen=True)
class CategorySpec:
    slug: str
    name: str
    sort_order: int
    deposit: Decimal


@dataclass(frozen=True)
class CarSpec:
    registration_number: str
    category_slug: str
    make: str
    model: str
    year: int
    color: str
    fuel_type: str
    mileage: int
    seats: int
    status: str = CarStatus.ACTIVE


@dataclass(frozen=True)
class CustomerSpec:
    email: str
    first_name: str
    last_name: str
    phone: str
    company_name: str = ""
    city: str = ""


@dataclass(frozen=True)
class ScenarioSpec:
    key: str
    car_registration: str
    customer_email: str
    start_offset_days: int
    end_offset_days: int
    reservation_status: str
    rental_state: str | None = None
    extra_codes: tuple[str, ...] = ()
    cancel_reason: str = ""


CATEGORIES: tuple[CategorySpec, ...] = (
    CategorySpec("kompakt", "Kompakt", 1, Decimal("1500.00")),
    CategorySpec("suv", "SUV", 2, Decimal("3000.00")),
    CategorySpec("premium", "Premium", 3, Decimal("5000.00")),
)

CARS: tuple[CarSpec, ...] = (
    CarSpec(
        "KR1DEMO1",
        "kompakt",
        "Toyota",
        "Yaris",
        2022,
        "bialy",
        FuelType.PETROL,
        48_200,
        5,
    ),
    CarSpec(
        "KR1DEMO2",
        "kompakt",
        "Volkswagen",
        "Polo",
        2021,
        "szary",
        FuelType.PETROL,
        62_400,
        5,
    ),
    CarSpec(
        "KR1DEMO3", "suv", "Skoda", "Kodiaq", 2023, "czarny", FuelType.DIESEL, 38_900, 5
    ),
    CarSpec(
        "KR1DEMO4",
        "suv",
        "Hyundai",
        "Tucson",
        2022,
        "srebrny",
        FuelType.HYBRID,
        41_500,
        5,
    ),
    CarSpec(
        "KR1DEMO5",
        "kompakt",
        "Ford",
        "Focus",
        2020,
        "niebieski",
        FuelType.PETROL,
        71_000,
        5,
    ),
    CarSpec(
        "KR1DEMO6", "premium", "BMW", "320i", 2023, "grafit", FuelType.PETROL, 22_100, 5
    ),
    CarSpec(
        "KR1DEMO7", "premium", "Audi", "A4", 2021, "bialy", FuelType.DIESEL, 55_800, 5
    ),
    CarSpec(
        "KR1DEMO8",
        "kompakt",
        "Renault",
        "Clio",
        2019,
        "czerwony",
        FuelType.PETROL,
        89_300,
        5,
    ),
    CarSpec(
        "KR1DEMO9",
        "kompakt",
        "Opel",
        "Corsa",
        2018,
        "szary",
        FuelType.PETROL,
        102_000,
        5,
        status=CarStatus.INACTIVE,
    ),
    CarSpec(
        "KR1DEM10",
        "suv",
        "Nissan",
        "Qashqai",
        2017,
        "braz",
        FuelType.DIESEL,
        118_500,
        5,
        status=CarStatus.RETIRED,
    ),
)

CUSTOMERS: tuple[CustomerSpec, ...] = (
    CustomerSpec(
        "jan.kowalski@demo.pl", "Jan", "Kowalski", "+48111111111", city="Krakow"
    ),
    CustomerSpec(
        "anna.nowak@demo.pl",
        "Anna",
        "Nowak",
        "+48222222222",
        company_name="Nowak Transport",
        city="Krakow",
    ),
    CustomerSpec(
        "piotr.wisniewski@demo.pl",
        "Piotr",
        "Wisniewski",
        "+48333333333",
        city="Warszawa",
    ),
    CustomerSpec(
        "maria.kowalczyk@demo.pl", "Maria", "Kowalczyk", "+48444444444", city="Gdansk"
    ),
    CustomerSpec(
        "biuro@logistyka-demo.pl",
        "Tomasz",
        "Zajac",
        "+48555555555",
        company_name="Logistyka Demo Sp. z o.o.",
        city="Katowice",
    ),
    CustomerSpec("ewa.lis@demo.pl", "Ewa", "Lis", "+48666666666", city="Wroclaw"),
    CustomerSpec(
        "michal.baran@demo.pl", "Michal", "Baran", "+48777777777", city="Poznan"
    ),
    CustomerSpec(
        "katarzyna.sokol@demo.pl", "Katarzyna", "Sokol", "+48888888888", city="Lodz"
    ),
)

SCENARIOS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec(
        "history-closed-1",
        "KR1DEMO1",
        "jan.kowalski@demo.pl",
        -40,
        -35,
        ReservationStatus.CONFIRMED,
        rental_state="closed",
    ),
    ScenarioSpec(
        "history-closed-2",
        "KR1DEMO2",
        "piotr.wisniewski@demo.pl",
        -70,
        -63,
        ReservationStatus.CONFIRMED,
        rental_state="closed",
        extra_codes=("child_seat",),
    ),
    ScenarioSpec(
        "ops-returned",
        "KR1DEMO3",
        "maria.kowalczyk@demo.pl",
        -10,
        -2,
        ReservationStatus.CONFIRMED,
        rental_state="returned",
    ),
    ScenarioSpec(
        "ops-active",
        "KR1DEMO4",
        "biuro@logistyka-demo.pl",
        -2,
        5,
        ReservationStatus.CONFIRMED,
        rental_state="active",
    ),
    ScenarioSpec(
        "ops-scheduled-near",
        "KR1DEMO5",
        "anna.nowak@demo.pl",
        3,
        8,
        ReservationStatus.CONFIRMED,
        rental_state="scheduled",
        extra_codes=("child_seat",),
    ),
    ScenarioSpec(
        "ops-scheduled-far",
        "KR1DEMO6",
        "ewa.lis@demo.pl",
        12,
        18,
        ReservationStatus.CONFIRMED,
        rental_state="scheduled",
    ),
    ScenarioSpec(
        "res-confirmed-future",
        "KR1DEMO7",
        "michal.baran@demo.pl",
        25,
        30,
        ReservationStatus.CONFIRMED,
    ),
    ScenarioSpec(
        "res-pending-payment",
        "KR1DEMO8",
        "katarzyna.sokol@demo.pl",
        35,
        38,
        ReservationStatus.PENDING_PAYMENT,
    ),
    ScenarioSpec(
        "res-cancelled",
        "KR1DEMO1",
        "ewa.lis@demo.pl",
        -20,
        -18,
        ReservationStatus.CANCELLED,
        cancel_reason="Klient zrezygnowal z terminu.",
    ),
    ScenarioSpec(
        "res-draft",
        "KR1DEMO8",
        "jan.kowalski@demo.pl",
        45,
        48,
        ReservationStatus.DRAFT,
    ),
)

DAILY_RATES: dict[str, Decimal] = {
    "kompakt": Decimal("120.00"),
    "suv": Decimal("180.00"),
    "premium": Decimal("260.00"),
}
