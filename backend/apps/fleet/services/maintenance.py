from datetime import datetime

from apps.fleet.models import AvailabilityBlock, AvailabilityBlockType, RepairRecord
from apps.fleet.services.availability import AvailabilityService


class FleetMaintenanceService:
    @staticmethod
    def create_availability_block(
        *,
        car_id: int,
        start_at: datetime,
        end_at: datetime,
        reason: str,
        block_type: str = AvailabilityBlockType.SERVICE,
        created_by_id: int | None = None,
    ) -> AvailabilityBlock:
        AvailabilityService.assert_no_overlapping_block(car_id, start_at, end_at)
        return AvailabilityBlock.objects.create(
            car_id=car_id,
            start_at=start_at,
            end_at=end_at,
            reason=reason,
            block_type=block_type,
            created_by_id=created_by_id,
        )

    @staticmethod
    def update_availability_block(
        block: AvailabilityBlock,
        *,
        start_at: datetime,
        end_at: datetime,
        reason: str | None = None,
        block_type: str | None = None,
    ) -> AvailabilityBlock:
        AvailabilityService.assert_no_overlapping_block(
            block.car_id,
            start_at,
            end_at,
            exclude_block_id=block.pk,
        )
        block.start_at = start_at
        block.end_at = end_at
        if reason is not None:
            block.reason = reason
        if block_type is not None:
            block.block_type = block_type
        block.save()
        return block

    @staticmethod
    def delete_availability_block(block: AvailabilityBlock) -> None:
        block.delete()

    @staticmethod
    def create_repair_record(**kwargs) -> RepairRecord:
        return RepairRecord.objects.create(**kwargs)
