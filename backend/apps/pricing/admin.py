from django.contrib import admin

from apps.pricing.models import DailyRate, ExtraService, PriceList, PricingRule


class DailyRateInline(admin.TabularInline):
    model = DailyRate
    extra = 0


class PricingRuleInline(admin.TabularInline):
    model = PricingRule
    extra = 0


class ExtraServiceInline(admin.TabularInline):
    model = ExtraService
    extra = 0


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "currency",
        "is_active",
        "is_default",
        "valid_from",
        "valid_to",
    )
    list_filter = ("is_active", "is_default", "currency")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (DailyRateInline, PricingRuleInline, ExtraServiceInline)
    readonly_fields = ("created_at", "updated_at")


@admin.register(DailyRate)
class DailyRateAdmin(admin.ModelAdmin):
    list_display = ("price_list", "category", "amount")
    list_filter = ("price_list",)


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = (
        "price_list",
        "name",
        "rule_type",
        "amount_type",
        "value",
        "priority",
        "is_active",
    )
    list_filter = ("price_list", "rule_type", "is_active")


@admin.register(ExtraService)
class ExtraServiceAdmin(admin.ModelAdmin):
    list_display = (
        "price_list",
        "code",
        "name",
        "charge_type",
        "amount",
        "is_active",
    )
    list_filter = ("price_list", "charge_type", "is_active")
