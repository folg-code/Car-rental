from django.contrib import admin

from apps.bookings.models import Customer


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
