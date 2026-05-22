from django.db.models import Prefetch, QuerySet

from apps.fleet.models import (
    AvailabilityBlock,
    Car,
    CarCategory,
    CarStatus,
    Damage,
    DamageStatus,
)


def get_car_by_id(car_id: int) -> Car | None:
    return Car.objects.select_related("category").filter(pk=car_id).first()


def get_car_detail(car_id: int) -> Car | None:
    return (
        Car.objects.select_related("category")
        .prefetch_related(
            Prefetch(
                "availability_blocks",
                queryset=AvailabilityBlock.objects.order_by("-start_at"),
            ),
            Prefetch(
                "damages",
                queryset=Damage.objects.order_by("-reported_at"),
            ),
            "images",
            "documents",
            "repairs",
        )
        .filter(pk=car_id)
        .first()
    )


def list_cars(*, status: str | None = None) -> QuerySet[Car]:
    qs = Car.objects.select_related("category").order_by("make", "model")
    if status:
        qs = qs.filter(status=status)
    return qs


def list_active_cars() -> QuerySet[Car]:
    return list_cars(status=CarStatus.ACTIVE)


def list_categories() -> QuerySet[CarCategory]:
    return CarCategory.objects.order_by("sort_order", "name")


def list_active_damages_for_car(car_id: int) -> QuerySet[Damage]:
    return Damage.objects.filter(car_id=car_id, status=DamageStatus.ACTIVE).order_by(
        "-reported_at"
    )
