from django.db import migrations


def seed_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("documents", "DocumentTemplate")
    templates = (
        (
            "Protokol wydania v1",
            "handover-v1",
            "handover_protocol_pdf",
            "documents/pdf/handover_protocol.html",
        ),
        (
            "Protokol zwrotu v1",
            "return-v1",
            "return_protocol_pdf",
            "documents/pdf/return_protocol.html",
        ),
        (
            "Faktura v1",
            "invoice-v1",
            "invoice_pdf",
            "documents/pdf/invoice.html",
        ),
    )
    for name, slug, document_type, template_path in templates:
        DocumentTemplate.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "document_type": document_type,
                "template_path": template_path,
                "is_active": True,
            },
        )


def unseed_templates(apps, schema_editor):
    DocumentTemplate = apps.get_model("documents", "DocumentTemplate")
    DocumentTemplate.objects.filter(
        slug__in=("handover-v1", "return-v1", "invoice-v1")
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0003_alter_document_file"),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]
