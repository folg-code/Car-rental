from django.contrib import admin

from apps.payments.models import Payment, PaymentIntent, PaymentProviderEvent


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "rental",
        "reservation",
        "amount",
        "payment_type",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_type")
    raw_id_fields = ("rental", "reservation")
    inlines = (PaymentInline,)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "rental",
        "payment_type",
        "method",
        "amount",
        "paid_at",
        "recorded_by",
    )
    list_filter = ("payment_type", "method")
    raw_id_fields = ("rental", "reservation", "intent", "recorded_by")
    date_hierarchy = "paid_at"


@admin.register(PaymentProviderEvent)
class PaymentProviderEventAdmin(admin.ModelAdmin):
    list_display = ("provider_event_id", "intent", "event_type", "received_at")
    raw_id_fields = ("intent",)
