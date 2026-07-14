from dataclasses import dataclass

from apps.fleet.models import Damage, DamageStatus
from apps.operations.models import DamageSnapshot, HandoverProtocol


@dataclass(frozen=True)
class DamageComparisonRow:
    source_damage_id: int | None
    handover_description: str | None
    handover_location: str | None
    handover_severity: str | None
    handover_is_new: bool
    return_description: str | None
    return_location: str | None
    return_severity: str | None
    status: str


def get_return_damage_comparison(
    handover: HandoverProtocol,
) -> list[DamageComparisonRow]:
    """Porownanie snapshotow wydania z aktywnymi szkodami floty przy zwrocie."""
    car = handover.rental.reservation.car
    handover_snaps: list[DamageSnapshot] = list(
        handover.damage_snapshots.order_by("captured_at", "pk")
    )
    active_damages = {
        damage.pk: damage
        for damage in Damage.objects.filter(car=car, status=DamageStatus.ACTIVE)
    }
    matched_active_ids: set[int] = set()
    rows: list[DamageComparisonRow] = []

    for snap in handover_snaps:
        source_id = snap.source_damage_id
        active = active_damages.get(source_id) if source_id else None
        if active is not None:
            matched_active_ids.add(source_id)
            changed = (
                snap.description != active.description
                or snap.location != active.location
                or snap.severity != active.severity
            )
            rows.append(
                DamageComparisonRow(
                    source_damage_id=source_id,
                    handover_description=snap.description,
                    handover_location=snap.location,
                    handover_severity=snap.severity,
                    handover_is_new=snap.is_new_at_protocol,
                    return_description=active.description,
                    return_location=active.location,
                    return_severity=active.severity,
                    status="changed" if changed else "unchanged",
                )
            )
        else:
            rows.append(
                DamageComparisonRow(
                    source_damage_id=source_id,
                    handover_description=snap.description,
                    handover_location=snap.location,
                    handover_severity=snap.severity,
                    handover_is_new=snap.is_new_at_protocol,
                    return_description=None,
                    return_location=None,
                    return_severity=None,
                    status="resolved",
                )
            )

    for damage_id, damage in active_damages.items():
        if damage_id in matched_active_ids:
            continue
        rows.append(
            DamageComparisonRow(
                source_damage_id=damage_id,
                handover_description=None,
                handover_location=None,
                handover_severity=None,
                handover_is_new=False,
                return_description=damage.description,
                return_location=damage.location,
                return_severity=damage.severity,
                status="new_at_return",
            )
        )

    return rows
