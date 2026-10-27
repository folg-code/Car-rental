from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.fleet.fuel import (
    FuelLevel,
    fuel_delta_liters,
    fuel_delta_liters_from_percent,
    fuel_level_to_liters,
    percent_to_fuel_level,
    percent_to_liters,
)
from apps.fleet.models import (
    Car,
    CarCategory,
    CarEquipment,
    Damage,
    DamageType,
    EquipmentItem,
    FuelType,
)


@pytest.mark.django_db
def test_car_tank_capacity_required_for_petrol() -> None:
    category = CarCategory.objects.create(name="Kompakt", slug="kompakt-t")
    car = Car(
        category=category,
        registration_number="TESTTANK1",
        make="Toyota",
        model="Yaris",
        year=2022,
        fuel_type=FuelType.PETROL,
        fuel_tank_capacity_liters=None,
    )
    with pytest.raises(ValidationError):
        car.full_clean()


@pytest.mark.django_db
def test_car_tank_capacity_optional_for_ev() -> None:
    category = CarCategory.objects.create(name="EV", slug="ev-t")
    car = Car(
        category=category,
        registration_number="TESTEV1",
        make="Tesla",
        model="Model 3",
        year=2023,
        fuel_type=FuelType.ELECTRIC,
        fuel_tank_capacity_liters=None,
    )
    car.full_clean()


@pytest.mark.django_db
def test_car_equipment_unique_per_item() -> None:
    category = CarCategory.objects.create(name="Kompakt", slug="kompakt-eq")
    car = Car.objects.create(
        category=category,
        registration_number="TESTEQ1",
        make="VW",
        model="Polo",
        year=2021,
        fuel_type=FuelType.PETROL,
        fuel_tank_capacity_liters=Decimal("40.0"),
    )
    item = EquipmentItem.objects.create(code="main_key", name="Kluczyk")
    CarEquipment.objects.create(car=car, item=item, quantity=1)
    with pytest.raises(IntegrityError):
        CarEquipment.objects.create(car=car, item=item, quantity=2)


@pytest.mark.django_db
def test_damage_diagram_fields() -> None:
    category = CarCategory.objects.create(name="Kompakt", slug="kompakt-dmg")
    car = Car.objects.create(
        category=category,
        registration_number="TESTDMG1",
        make="Ford",
        model="Focus",
        year=2020,
        fuel_type=FuelType.PETROL,
        fuel_tank_capacity_liters=Decimal("47.0"),
    )
    damage = Damage.objects.create(
        car=car,
        description="Rysa",
        damage_type=DamageType.SCRATCH,
        pos_x=Decimal("30.5"),
        pos_y=Decimal("40.0"),
    )
    assert damage.diagram_letter == "R"


def test_fuel_level_helpers() -> None:
    assert percent_to_liters(50, Decimal("40.0")) == Decimal("20.0")
    assert fuel_level_to_liters(FuelLevel.HALF.value, Decimal("40.0")) == Decimal(
        "20.0"
    )
    assert fuel_delta_liters(
        handover_level=FuelLevel.FULL.value,
        return_level=FuelLevel.HALF.value,
        tank_capacity_liters=Decimal("40.0"),
    ) == Decimal("20.0")
    assert fuel_delta_liters_from_percent(
        handover_percent=100,
        return_percent=70,
        tank_capacity_liters=Decimal("50.0"),
    ) == Decimal("15.0")
    assert percent_to_fuel_level(50) == FuelLevel.HALF.value
