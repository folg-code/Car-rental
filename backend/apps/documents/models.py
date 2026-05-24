import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.validators import MinValueValidator
from django.db import models


def private_document_storage():
    return storages["private_documents"]


class DocumentType(models.TextChoices):
    HANDOVER_PROTOCOL_PDF = "handover_protocol_pdf", "PDF protokolu wydania"
    RETURN_PROTOCOL_PDF = "return_protocol_pdf", "PDF protokolu zwrotu"
    INVOICE_PDF = "invoice_pdf", "PDF faktury"
    RENTAL_CONTRACT_PDF = "rental_contract_pdf", "PDF umowy wynajmu"


class EmailStatus(models.TextChoices):
    PENDING = "pending", "Oczekuje"
    SENT = "sent", "Wyslany"
    FAILED = "failed", "Blad"


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Szkic"
    ISSUED = "issued", "Wystawiona"
    PAID = "paid", "Oplacona"
    CANCELLED = "cancelled", "Anulowana"


def document_upload_path(instance: "Document", filename: str) -> str:
    from django.utils import timezone

    when = instance.generated_at or timezone.now()
    date_part = when.strftime("%Y/%m")
    return f"{instance.document_type}/{date_part}/{instance.uuid}_{filename}"


class DocumentTemplate(models.Model):
    """Szablon HTML do renderowania PDF
    — wersjonowany przez nowe rekordy, nie nadpisaniem."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80, unique=True)
    document_type = models.CharField(max_length=40, choices=DocumentType.choices)
    template_path = models.CharField(
        max_length=255,
        help_text="Sciezka szablonu Django, np. documents/pdf/handover_protocol.html",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["document_type", "slug"]
        verbose_name = "szablon dokumentu"
        verbose_name_plural = "szablony dokumentow"

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class Document(models.Model):
    """
    Wygenerowany plik dokumentu — niemutowalny po utworzeniu.

    Powiazania opcjonalne; typ dokumentu okresla wymagane FK (walidacja w clean).
    """

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    document_type = models.CharField(max_length=40, choices=DocumentType.choices)
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    rental = models.ForeignKey(
        "bookings.Rental",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    customer = models.ForeignKey(
        "bookings.Customer",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    handover_protocol = models.ForeignKey(
        "operations.HandoverProtocol",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    return_protocol = models.ForeignKey(
        "operations.ReturnProtocol",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    invoice = models.ForeignKey(
        "documents.Invoice",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="document_files",
    )
    file = models.FileField(
        upload_to=document_upload_path,
        storage=private_document_storage,
    )
    content_type = models.CharField(max_length=100, default="application/pdf")
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hex skrotu pliku.",
    )
    file_size_bytes = models.PositiveIntegerField(default=0)
    version = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=200, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_generated",
    )

    class Meta:
        ordering = ["-generated_at"]
        verbose_name = "dokument"
        verbose_name_plural = "dokumenty"
        indexes = [
            models.Index(fields=["rental", "document_type"]),
            models.Index(fields=["document_type", "generated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_document_type_display()} — {self.uuid}"

    def clean(self) -> None:
        super().clean()
        if self.document_type == DocumentType.HANDOVER_PROTOCOL_PDF:
            if not self.handover_protocol_id:
                raise ValidationError(
                    {"handover_protocol": "PDF wydania wymaga protokolu wydania."}
                )
        elif self.document_type == DocumentType.RETURN_PROTOCOL_PDF:
            if not self.return_protocol_id:
                raise ValidationError(
                    {"return_protocol": "PDF zwrotu wymaga protokolu zwrotu."}
                )
        elif self.document_type == DocumentType.INVOICE_PDF:
            if not self.invoice_id:
                raise ValidationError({"invoice": "PDF faktury wymaga faktury."})

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            previous_file = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("file", flat=True)
                .first()
            )
            if previous_file and self.file.name != previous_file:
                raise ValidationError(
                    "Plik dokumentu nie moze byc zmieniony po utworzeniu."
                )
        self.full_clean()
        super().save(*args, **kwargs)


class EmailLog(models.Model):
    """Log wysylek emaili z dokumentami — retry przez EmailService, nie w szablonie."""

    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="email_logs",
    )
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails_sent",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "log email"
        verbose_name_plural = "logi email"

    def __str__(self) -> str:
        return f"{self.recipient_email} — {self.get_status_display()}"


class Invoice(models.Model):
    """
    Faktura ksiegowa — oddzielona od Payment.

    Pozycje z PriceLine / ustalonych kwot; bez przeliczania cennika w documents.
    """

    rental = models.ForeignKey(
        "bookings.Rental",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    customer = models.ForeignKey(
        "bookings.Customer",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=32, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True,
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        default=Decimal("0"),
    )
    currency = models.CharField(max_length=3, default="PLN")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-pk"]
        verbose_name = "faktura"
        verbose_name_plural = "faktury"

    def __str__(self) -> str:
        return f"Faktura {self.invoice_number} — {self.total_amount} {self.currency}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    price_line = models.ForeignKey(
        "bookings.PriceLine",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_items",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "pk"]
        verbose_name = "pozycja faktury"
        verbose_name_plural = "pozycje faktury"

    def __str__(self) -> str:
        return f"{self.description} — {self.line_total}"

    def clean(self) -> None:
        super().clean()
        expected = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        if self.line_total != expected:
            raise ValidationError(
                {"line_total": "Suma pozycji musi rownac quantity * unit_price."}
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
