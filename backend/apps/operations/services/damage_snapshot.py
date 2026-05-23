from django.utils import timezone

from apps.fleet.models import Damage, DamageStatus
from apps.operations.models import DamageSnapshot, HandoverProtocol, ReturnProtocol


class DamageSnapshotService:
    @staticmethod
    def freeze_active_damages_for_handover(
        handover: HandoverProtocol,
    ) -> list[DamageSnapshot]:
        car = handover.rental.reservation.car
        snapshots: list[DamageSnapshot] = []
        for damage in Damage.objects.filter(car=car, status=DamageStatus.ACTIVE):
            snap = DamageSnapshot.objects.create(
                handover=handover,
                source_damage=damage,
                description=damage.description,
                location=damage.location,
                severity=damage.severity,
                status_at_capture=damage.status,
                is_new_at_protocol=False,
                captured_at=timezone.now(),
            )
            snapshots.append(snap)
        return snapshots

    @staticmethod
    def freeze_active_damages_for_return(
        return_protocol: ReturnProtocol,
    ) -> list[DamageSnapshot]:
        car = return_protocol.rental.reservation.car
        snapshots: list[DamageSnapshot] = []
        for damage in Damage.objects.filter(car=car, status=DamageStatus.ACTIVE):
            snap = DamageSnapshot.objects.create(
                return_protocol=return_protocol,
                source_damage=damage,
                description=damage.description,
                location=damage.location,
                severity=damage.severity,
                status_at_capture=damage.status,
                is_new_at_protocol=False,
                captured_at=timezone.now(),
            )
            snapshots.append(snap)
        return snapshots

    @staticmethod
    def snapshot_new_damage(
        *,
        handover: HandoverProtocol | None = None,
        return_protocol: ReturnProtocol | None = None,
        damage: Damage,
    ) -> DamageSnapshot:
        if handover is not None:
            return DamageSnapshot.objects.create(
                handover=handover,
                source_damage=damage,
                description=damage.description,
                location=damage.location,
                severity=damage.severity,
                status_at_capture=damage.status,
                is_new_at_protocol=True,
            )
        if return_protocol is not None:
            return DamageSnapshot.objects.create(
                return_protocol=return_protocol,
                source_damage=damage,
                description=damage.description,
                location=damage.location,
                severity=damage.severity,
                status_at_capture=damage.status,
                is_new_at_protocol=True,
            )
        msg = "Wymagany protokol wydania lub zwrotu."
        raise ValueError(msg)
