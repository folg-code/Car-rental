from django.contrib import admin

from apps.bookings.models import Customer, PriceLine, Rental, Reservation


class PriceLineInline(admin.TabularInline):
    model = PriceLine
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "email",
        "phone",
        "company_name",
        "user",
        "created_at",
    )
    list_filter = ("country",)
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "company_name",
        "tax_id",
    )
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "car",
        "start_at",
        "end_at",
        "status",
        "pricing_mode",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "customer__last_name",
        "customer__first_name",
        "customer__email",
        "car__registration_number",
    )
    raw_id_fields = ("customer", "car", "created_by", "price_list")
    readonly_fields = ("created_at", "updated_at", "cancelled_at")
    date_hierarchy = "start_at"
    inlines = (PriceLineInline,)


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reservation",
        "status",
        "scheduled_start_at",
        "scheduled_end_at",
        "deposit_amount",
        "created_at",
    )
    list_filter = ("status",)
    raw_id_fields = ("reservation", "created_by")
    readonly_fields = (
        "created_at",
        "updated_at",
        "actual_start_at",
        "actual_end_at",
        "closed_at",
        "cancelled_at",
    )
    date_hierarchy = "scheduled_start_at"
