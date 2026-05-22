from django.contrib import admin

from apps.fleet.models import (
    AvailabilityBlock,
    Car,
    CarCategory,
    CarDocument,
    CarImage,
    Damage,
    RepairRecord,
)


@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "deposit", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 0


class CarDocumentInline(admin.TabularInline):
    model = CarDocument
    extra = 0


class AvailabilityBlockInline(admin.TabularInline):
    model = AvailabilityBlock
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "make",
        "model",
        "year",
        "category",
        "status",
        "mileage",
    )
    list_filter = ("status", "category", "fuel_type")
    search_fields = ("registration_number", "make", "model", "vin")
    inlines = [CarImageInline, CarDocumentInline, AvailabilityBlockInline]


@admin.register(AvailabilityBlock)
class AvailabilityBlockAdmin(admin.ModelAdmin):
    list_display = ("car", "block_type", "start_at", "end_at", "reason")
    list_filter = ("block_type",)
    raw_id_fields = ("car", "created_by")


@admin.register(Damage)
class DamageAdmin(admin.ModelAdmin):
    list_display = ("car", "severity", "status", "reported_at", "location")
    list_filter = ("severity", "status")
    search_fields = ("description", "location")
    raw_id_fields = ("car",)


@admin.register(RepairRecord)
class RepairRecordAdmin(admin.ModelAdmin):
    list_display = ("car", "performed_at", "mileage_at_service", "cost")
    raw_id_fields = ("car",)
