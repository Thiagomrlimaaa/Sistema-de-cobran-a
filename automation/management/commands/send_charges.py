from django.core.management.base import BaseCommand

from automation.tasks import send_charge_messages


class Command(BaseCommand):
    help = "Envia mensagens de cobrança para clientes (dia 10)."

    def handle(self, *args, **options):
        processed = send_charge_messages()
        self.stdout.write(self.style.SUCCESS(f"Cobranças enviadas: {processed}"))

