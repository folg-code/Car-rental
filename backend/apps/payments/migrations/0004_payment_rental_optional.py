import django
import django.db.models.deletion
from django.db import migrations, models


def _payment_target_constraint() -> models.CheckConstraint:
    q = models.Q(
        ("rental__isnull", False),
        ("reservation__isnull", False),
        _connector="OR",
    )
    kw = "condition" if django.VERSION >= (5, 1) else "check"
    return models.CheckConstraint(
        **{kw: q},
        name="payment_requires_rental_or_reservation",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0003_provider_event_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="rental",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="payments",
                to="bookings.rental",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=_payment_target_constraint(),
        ),
    ]
