from django.contrib import admin

from apps.website.models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "user", "created_at", "updated_at")
    search_fields = ("session_key",)
    readonly_fields = ("session_key", "created_at", "updated_at")
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("content",)
    readonly_fields = ("session", "role", "content", "created_at")
