# Generated during VPS deploy hardening on 2026-07-15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0004_seed_document_templates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="file_hash",
            field=models.CharField(
                blank=True,
                help_text="SHA-256 hex skrotu kanonicznej tresci HTML dokumentu.",
                max_length=64,
            ),
        ),
    ]
