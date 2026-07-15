from datetime import date

from django.db.models import Count, Q, QuerySet

from apps.pricing.models import (
    POST_RENTAL_EXTRA_CODES,
    DailyRate,
    ExtraService,
    PriceList,
    PricingRule,
)


def list_price_lists() -> QuerySet[PriceList]:
    return PriceList.objects.annotate(
        rates_count=Count("daily_rates", distinct=True),
        rules_count=Count("rules", distinct=True),
        extras_count=Count("extra_services", distinct=True),
    ).order_by("-is_default", "-is_active", "name")


def get_price_list_by_id(price_list_id: int) -> PriceList | None:
    return (
        PriceList.objects.filter(pk=price_list_id)
        .prefetch_related(
            "daily_rates__category",
            "rules",
            "extra_services",
        )
        .first()
    )


def get_active_price_lists() -> QuerySet[PriceList]:
    return PriceList.objects.filter(is_active=True).order_by("-is_default", "name")


def get_price_list_for_date(on_date: date) -> PriceList | None:
    """Cennik obowiazujacy w podanym dniu (domyslny jako fallback)."""
    matching = get_active_price_lists().filter(
        Q(valid_from__isnull=True) | Q(valid_from__lte=on_date),
        Q(valid_to__isnull=True) | Q(valid_to__gte=on_date),
    )
    selected = matching.first()
    if selected is not None:
        return selected
    return get_active_price_lists().filter(is_default=True).first()


def get_daily_rate(price_list: PriceList, category_id: int) -> DailyRate | None:
    return (
        DailyRate.objects.filter(price_list=price_list, category_id=category_id)
        .select_related("category")
        .first()
    )


def get_active_rules(price_list: PriceList) -> QuerySet[PricingRule]:
    return price_list.rules.filter(is_active=True).order_by("priority", "pk")


def get_extra_by_code(price_list: PriceList, code: str) -> ExtraService | None:
    return (
        price_list.extra_services.filter(code=code, is_active=True)
        .order_by("sort_order")
        .first()
    )


def list_active_extras(price_list: PriceList) -> QuerySet[ExtraService]:
    return price_list.extra_services.filter(is_active=True).order_by(
        "sort_order", "name"
    )


def list_bookable_extras(price_list: PriceList) -> QuerySet[ExtraService]:
    """Usługi wybieralne przy rezerwacji (bez naliczeń po najmie)."""
    return list_active_extras(price_list).exclude(
        code__in=POST_RENTAL_EXTRA_CODES,
    )
