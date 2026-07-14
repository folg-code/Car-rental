# Generated manually for task 9.3

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0002_paymentintent_reservation"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentproviderevent",
            name="provider_event_id",
            field=models.CharField(default="legacy", max_length=128, unique=True),
            preserve_default=False,
        ),
    ]
