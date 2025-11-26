from __future__ import annotations

import logging
from typing import Iterable, Optional

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from clients.models import Client
from messaging.models import MessageLog, MessageTemplate
from messaging.services import send_message_to_client

logger = logging.getLogger(__name__)

REMINDER_TEMPLATE_CODE = "reminder"
CHARGE_TEMPLATE_CODE = "charge"


def _eligible_clients(due_day: int, statuses: Optional[Iterable[str]] = None) -> Iterable[Client]:
    today = timezone.localdate()
    if today.day != due_day:
        logger.info("Dia atual %s diferente do dia configurado %s. Nenhum envio automático.", today.day, due_day)
        return []

    queryset = Client.objects.all()
    if statuses:
        queryset = queryset.filter(status__in=list(statuses))
    date_filter = Q(
        due_date__year=today.year,
        due_date__month=today.month,
        due_date__day=due_day,
    ) | Q(due_date__isnull=True, due_day=due_day)
    return queryset.filter(date_filter)


@shared_task
def send_reminder_messages() -> int:
    logger.info("Iniciando envio de lembretes (dia 05).")
    template_exists = MessageTemplate.objects.filter(code=REMINDER_TEMPLATE_CODE, is_active=True).exists()
    if not template_exists:
        logger.warning("Template de lembrete não encontrado. Abortando envio.")
        return 0

    clients = _eligible_clients(5, statuses=[Client.Status.ACTIVE, Client.Status.DELINQUENT])
    sent_count = 0
    for client in clients:
        send_message_to_client(
            client=client,
            template_code=REMINDER_TEMPLATE_CODE,
            message_type=MessageLog.Type.REMINDER,
        )
        sent_count += 1
    logger.info("Envio de lembretes concluído. Total: %s", sent_count)
    return sent_count


@shared_task
def send_charge_messages() -> int:
    logger.info("Iniciando envio de cobranças (dia 10).")
    template_exists = MessageTemplate.objects.filter(code=CHARGE_TEMPLATE_CODE, is_active=True).exists()
    if not template_exists:
        logger.warning("Template de cobrança não encontrado. Abortando envio.")
        return 0

    clients = _eligible_clients(10, statuses=[Client.Status.ACTIVE, Client.Status.DELINQUENT])
    sent_count = 0
    for client in clients:
        send_message_to_client(
            client=client,
            template_code=CHARGE_TEMPLATE_CODE,
            message_type=MessageLog.Type.CHARGE,
        )
        sent_count += 1
    logger.info("Envio de cobranças concluído. Total: %s", sent_count)
    return sent_count

