from django.contrib import admin

from apps.bookings.models import Customer, Reservation


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
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "customer__last_name",
        "customer__first_name",
        "customer__email",
        "car__registration_number",
    )
    raw_id_fields = ("customer", "car", "created_by")
    readonly_fields = ("created_at", "updated_at", "cancelled_at")
    date_hierarchy = "start_at"
