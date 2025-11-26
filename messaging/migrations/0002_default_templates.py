from django.db import migrations


REMINDER_TEMPLATE = {
    "code": "reminder",
    "name": "Lembrete de pagamento",
    "channel": "whatsapp",
    "body": (
        "Olá {{nome}}, tudo bem?\n"
        "Lembrando que sua mensalidade no valor de R$ {{valor}} vence no dia {{vencimento}}.\n"
        "Evite atrasos e mantenha seu acesso ativo. 💼"
    ),
}

CHARGE_TEMPLATE = {
    "code": "charge",
    "name": "Cobrança por atraso",
    "channel": "whatsapp",
    "body": (
        "Olá {{nome}}, notamos que o pagamento da sua mensalidade ainda não foi identificado.\n"
        "Evite a suspensão do serviço e realize o pagamento o quanto antes.\n"
        "Caso já tenha pago, desconsidere esta mensagem. 📩"
    ),
}


def create_default_templates(apps, schema_editor):
    MessageTemplate = apps.get_model("messaging", "MessageTemplate")
    for template_data in (REMINDER_TEMPLATE, CHARGE_TEMPLATE):
        MessageTemplate.objects.update_or_create(
            code=template_data["code"],
            defaults={
                "name": template_data["name"],
                "channel": template_data["channel"],
                "body": template_data["body"],
                "is_active": True,
            },
        )


def delete_default_templates(apps, schema_editor):
    MessageTemplate = apps.get_model("messaging", "MessageTemplate")
    MessageTemplate.objects.filter(code__in=["reminder", "charge"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_templates, delete_default_templates),
    ]

