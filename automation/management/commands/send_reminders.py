from django.core.management.base import BaseCommand

from automation.tasks import send_reminder_messages


class Command(BaseCommand):
    help = "Envia mensagens de lembrete para clientes (dia 05)."

    def handle(self, *args, **options):
        processed = send_reminder_messages()
        self.stdout.write(self.style.SUCCESS(f"Lembretes enviados: {processed}"))

