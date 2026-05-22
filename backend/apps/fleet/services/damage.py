from apps.fleet.models import Damage, DamagePhoto, DamageStatus


class DamageService:
    @staticmethod
    def report_damage(**kwargs) -> Damage:
        return Damage.objects.create(**kwargs)

    @staticmethod
    def mark_repaired(damage: Damage) -> Damage:
        from django.utils import timezone

        damage.status = DamageStatus.REPAIRED
        damage.repaired_at = timezone.now()
        damage.save(update_fields=["status", "repaired_at"])
        return damage

    @staticmethod
    def add_photo(damage: Damage, *, image) -> DamagePhoto:
        return DamagePhoto.objects.create(damage=damage, image=image)
