from django.contrib import admin

from apps.notifications.models import SmsLog


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "recipient_phone",
        "status",
        "reservation",
        "document",
        "sent_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("recipient_phone", "body", "external_id")
    readonly_fields = (
        "reservation",
        "document",
        "recipient_phone",
        "body",
        "status",
        "error_message",
        "external_id",
        "sent_at",
        "sent_by",
        "created_at",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
