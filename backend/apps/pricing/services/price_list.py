from django.db import transaction

from apps.pricing.models import DailyRate, ExtraService, PriceList, PricingRule


class PriceListService:
    @staticmethod
    @transaction.atomic
    def save_price_list(price_list: PriceList) -> PriceList:
        price_list.full_clean()
        if price_list.is_default:
            PriceList.objects.exclude(pk=price_list.pk).update(is_default=False)
        price_list.save()
        return price_list

    @staticmethod
    def add_daily_rate(*, price_list: PriceList, category_id: int, amount) -> DailyRate:
        rate = DailyRate(
            price_list=price_list,
            category_id=category_id,
            amount=amount,
        )
        rate.save()
        return rate

    @staticmethod
    def add_rule(*, price_list: PriceList, **fields) -> PricingRule:
        rule = PricingRule(price_list=price_list, **fields)
        rule.save()
        return rule

    @staticmethod
    def add_extra(*, price_list: PriceList, **fields) -> ExtraService:
        extra = ExtraService(price_list=price_list, **fields)
        extra.save()
        return extra
