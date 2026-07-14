from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "actor",
        "reservation_id",
        "rental_id",
        "payment_id",
    )
    list_filter = ("action", "created_at")
    search_fields = (
        "rental_id",
        "reservation_id",
        "payment_id",
        "object_type",
    )
    readonly_fields = (
        "action",
        "actor",
        "reservation",
        "rental",
        "payment",
        "object_type",
        "object_id",
        "old_value",
        "new_value",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
