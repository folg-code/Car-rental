from django.contrib import admin

from apps.documents.models import (
    Document,
    DocumentTemplate,
    EmailLog,
    EmailStatus,
    Invoice,
    InvoiceItem,
)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


class EmailLogInline(admin.TabularInline):
    model = EmailLog
    extra = 0
    readonly_fields = ("created_at", "sent_at")


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "document_type", "is_active")
    list_filter = ("document_type", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "document_type",
        "rental",
        "version",
        "file_size_bytes",
        "generated_at",
    )
    list_filter = ("document_type",)
    readonly_fields = (
        "uuid",
        "file_hash",
        "file_size_bytes",
        "generated_at",
    )
    raw_id_fields = (
        "rental",
        "customer",
        "handover_protocol",
        "return_protocol",
        "invoice",
        "template",
        "generated_by",
    )
    inlines = (EmailLogInline,)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("recipient_email", "subject", "status", "sent_at", "created_at")
    list_filter = ("status",)
    raw_id_fields = ("document", "sent_by")
    actions = ("retry_failed_emails",)

    @admin.action(description="Ponów wysyłkę (tylko failed)")
    def retry_failed_emails(self, request, queryset):
        from apps.documents.tasks import retry_failed_document_email_task

        failed = queryset.filter(status=EmailStatus.FAILED)
        queued = 0
        for email_log in failed:
            retry_failed_document_email_task.delay(
                email_log.pk,
                sent_by_id=request.user.pk,
            )
            queued += 1
        self.message_user(
            request,
            f"Kolejkowano ponowienie wysyłki: {queued}.",
        )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "customer",
        "rental",
        "total_amount",
        "status",
        "issue_date",
    )
    list_filter = ("status",)
    raw_id_fields = ("rental", "customer")
    inlines = (InvoiceItemInline,)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "quantity", "unit_price", "line_total")
    raw_id_fields = ("invoice", "price_line")
