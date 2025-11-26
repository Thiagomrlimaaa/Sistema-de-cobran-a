from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from clients.models import Client
from .models import MessageLog, MessageTemplate

logger = logging.getLogger(__name__)


def _compute_due_date(client: Client, reference_date: Optional[date] = None) -> date:
    today = reference_date or timezone.localdate()
    if getattr(client, "due_date", None):
        return client.due_date

    days_in_month = monthrange(today.year, today.month)[1]
    day = min(client.due_day, days_in_month)
    return date(today.year, today.month, day)


def _render_message(template: MessageTemplate, client: Client, extra_context: Optional[Dict[str, Any]] = None) -> str:
    due_date = _compute_due_date(client)
    context = {
        "nome": client.name,
        "valor": f"{client.monthly_fee:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "vencimento": due_date.strftime("%d/%m/%Y"),
        "link_pagamento": client.payment_link or "",
    }
    if extra_context:
        context.update(extra_context)

    normalized_body = template.body.replace("{{", "{").replace("}}", "}")
    try:
        rendered = normalized_body.format(**context)
    except KeyError as exc:
        missing_key = exc.args[0]
        logger.exception("Chave de template ausente: %s", missing_key)
        raise ValueError(f"Chave de template ausente: {missing_key}") from exc
    return rendered


def _send_whatsapp_message(client: Client, message: str) -> Dict[str, Any]:
    provider = getattr(settings, "WHATSAPP_PROVIDER", "meta")

    if provider == "whapi":
        base_url = getattr(settings, "WHAPI_BASE_URL", "")
        token = getattr(settings, "WHAPI_TOKEN", "")
        channel_type = getattr(settings, "WHAPI_CHANNEL_TYPE", "web")

        if not token:
            raise ValueError("Token da WHAPI não configurado. Defina WHAPI_TOKEN.")

        url = f"{base_url.rstrip('/')}/messages/text"
        payload = {
            "to": client.formatted_phone,
            "body": message,
            "typing_time": 0,
            "channel_type": channel_type,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    elif provider == "infobip":
        base_url = getattr(settings, "INFOBIP_BASE_URL", "")
        api_key = getattr(settings, "INFOBIP_API_KEY", "")
        sender = getattr(settings, "INFOBIP_SENDER", "")

        if not all([base_url, api_key, sender]):
            raise ValueError("Configurações Infobip ausentes. Defina INFOBIP_BASE_URL, INFOBIP_API_KEY e INFOBIP_SENDER.")

        url = f"https://{base_url.rstrip('/')}/whatsapp/1/message/text"
        to_number = client.formatted_phone
        if not to_number.startswith("+"):
            to_number = f"+{to_number}"

        payload = {
            "from": sender,
            "to": to_number,
            "content": {"text": message},
        }
        headers = {
            "Authorization": f"App {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    else:
        api_url = getattr(settings, "WHATSAPP_API_URL", "")
        token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
        phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")

        if not all([api_url, token, phone_id]):
            raise ValueError("Configurações da API do WhatsApp (Meta) ausentes. Verifique as variáveis de ambiente.")

        url = f"{api_url.rstrip('/')}/{phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": client.formatted_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def _send_email_message(client: Client, subject: str, message: str) -> Dict[str, Any]:
    if not client.email:
        raise ValueError("Cliente não possui e-mail cadastrado.")

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@cobranca.local")
    send_mail(subject=subject, message=message, from_email=from_email, recipient_list=[client.email])
    return {"status": "email_sent"}


@transaction.atomic
def send_message_to_client(
    *,
    client: Client,
    template_code: str,
    message_type: str,
    extra_context: Optional[Dict[str, Any]] = None,
    initiated_by=None,
) -> MessageLog:
    template = MessageTemplate.objects.filter(code=template_code, is_active=True).first()
    if not template:
        raise ValueError(f"Template não encontrado ou inativo: {template_code}")

    message_body = _render_message(template, client, extra_context)

    payload = {
        "template": template.code,
        "message": message_body,
        "context": extra_context or {},
    }

    response_data: Dict[str, Any] = {}
    status = MessageLog.Status.SUCCESS
    error_message = ""

    try:
        if template.channel == MessageTemplate.Channel.WHATSAPP:
            response_data = _send_whatsapp_message(client, message_body)
        else:
            subject = f"Atualização de cobrança - {client.name}"
            response_data = _send_email_message(client, subject, message_body)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao enviar mensagem para %s", client)
        status = MessageLog.Status.FAILED
        error_message = str(exc)
        response_data = {"error": error_message}

    message_log = MessageLog.objects.create(
        client=client,
        template=template,
        message_type=message_type,
        channel=template.channel,
        status=status,
        payload=payload,
        response=response_data,
        error_message=error_message,
        created_by=initiated_by,
    )
    return message_log


def check_whatsapp_health() -> Dict[str, Any]:
    provider = getattr(settings, "WHATSAPP_PROVIDER", "meta")

    if provider == "whapi":
        base_url = getattr(settings, "WHAPI_BASE_URL", "")
        token = getattr(settings, "WHAPI_TOKEN", "")
        channel_type = getattr(settings, "WHAPI_CHANNEL_TYPE", "web")

        if not base_url:
            raise ValueError("WHAPI_BASE_URL não configurado.")
        if not token:
            raise ValueError("WHAPI_TOKEN não configurado.")

        url = f"{base_url.rstrip('/')}/health"
        params = {"wakeup": "true", "channel_type": channel_type}
        headers = {
            "Authorization": f"Bearer {token}",
            "accept": "application/json",
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return {
            "provider": "whapi",
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
        }

    api_url = getattr(settings, "WHATSAPP_API_URL", "")
    if not api_url:
        raise ValueError("WHATSAPP_API_URL não configurado para provider Meta.")

    phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
    token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")

    if not all([phone_id, token]):
        raise ValueError("WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_ACCESS_TOKEN são obrigatórios para provider Meta.")

    url = f"{api_url.rstrip('/')}/{phone_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return {
        "provider": "meta",
        "status_code": response.status_code,
        "data": response.json() if response.content else {},
    }

