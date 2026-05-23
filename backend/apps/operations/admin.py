from django.contrib import admin

from apps.operations.models import (
    DamageSnapshot,
    HandoverProtocol,
    ProtocolPhoto,
    ReturnProtocol,
    Signature,
)


class ProtocolPhotoInline(admin.TabularInline):
    model = ProtocolPhoto
    extra = 0


class DamageSnapshotInline(admin.TabularInline):
    model = DamageSnapshot
    extra = 0
    readonly_fields = ("captured_at",)


@admin.register(HandoverProtocol)
class HandoverProtocolAdmin(admin.ModelAdmin):
    list_display = ("rental", "mileage", "fuel_level_percent", "completed_at")
    raw_id_fields = ("rental", "completed_by")
    inlines = (ProtocolPhotoInline, DamageSnapshotInline)


@admin.register(ReturnProtocol)
class ReturnProtocolAdmin(admin.ModelAdmin):
    list_display = ("rental", "mileage", "fuel_level_percent", "completed_at")
    raw_id_fields = ("rental", "handover", "completed_by")
    inlines = (ProtocolPhotoInline, DamageSnapshotInline)


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ("signer_name", "signed_at", "handover", "return_protocol")
