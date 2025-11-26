import json

from django.core.management.base import BaseCommand, CommandError

from messaging.services import check_whatsapp_health


class Command(BaseCommand):
    help = "Verifica o status da integração WhatsApp (Meta ou WHAPI)."

    def handle(self, *args, **options):
        try:
            result = check_whatsapp_health()
        except Exception as exc:  # noqa: BLE001
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Verificação realizada com sucesso."))
        self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))

