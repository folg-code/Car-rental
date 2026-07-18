from django.contrib import admin

from apps.operations.models import (
    DamageSnapshot,
    HandoverProtocol,
    ProtocolDamageMarker,
    ProtocolDriver,
    ProtocolEquipmentLine,
    ProtocolPhoto,
    ProtocolSettlementLine,
    ReturnProtocol,
    Signature,
)


class ProtocolPhotoInline(admin.TabularInline):
    model = ProtocolPhoto
    extra = 0
    fk_name = "handover"


class ReturnProtocolPhotoInline(admin.TabularInline):
    model = ProtocolPhoto
    extra = 0
    fk_name = "return_protocol"


class DamageSnapshotInline(admin.TabularInline):
    model = DamageSnapshot
    extra = 0
    readonly_fields = ("captured_at",)
    fk_name = "handover"


class ReturnDamageSnapshotInline(admin.TabularInline):
    model = DamageSnapshot
    extra = 0
    readonly_fields = ("captured_at",)
    fk_name = "return_protocol"


class ProtocolDriverInline(admin.StackedInline):
    model = ProtocolDriver
    extra = 0


class ProtocolEquipmentInline(admin.TabularInline):
    model = ProtocolEquipmentLine
    extra = 0
    fk_name = "handover"


class ProtocolDamageMarkerInline(admin.TabularInline):
    model = ProtocolDamageMarker
    extra = 0
    fk_name = "handover"


@admin.register(HandoverProtocol)
class HandoverProtocolAdmin(admin.ModelAdmin):
    list_display = (
        "rental",
        "status",
        "mileage",
        "fuel_level",
        "fuel_level_percent",
        "completed_at",
    )
    list_filter = ("status",)
    raw_id_fields = ("rental", "completed_by")
    inlines = (
        ProtocolDriverInline,
        ProtocolPhotoInline,
        DamageSnapshotInline,
        ProtocolEquipmentInline,
        ProtocolDamageMarkerInline,
    )


@admin.register(ReturnProtocol)
class ReturnProtocolAdmin(admin.ModelAdmin):
    list_display = (
        "rental",
        "status",
        "mileage",
        "fuel_level",
        "completed_at",
    )
    list_filter = ("status",)
    raw_id_fields = ("rental", "handover", "completed_by")
    inlines = (ReturnProtocolPhotoInline, ReturnDamageSnapshotInline)


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = (
        "signer_name",
        "outcome",
        "signed_at",
        "handover",
        "return_protocol",
    )


@admin.register(ProtocolSettlementLine)
class ProtocolSettlementLineAdmin(admin.ModelAdmin):
    list_display = ("return_protocol", "code", "name", "amount", "decision")
    list_filter = ("decision", "code")
