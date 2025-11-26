from django.conf import settings
from django.db import models

from clients.models import Client


class MessageTemplate(models.Model):
    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"

    code = models.CharField("Código", max_length=50, unique=True)
    name = models.CharField("Nome", max_length=100)
    channel = models.CharField(
        "Canal",
        max_length=20,
        choices=Channel.choices,
        default=Channel.WHATSAPP,
    )
    body = models.TextField("Corpo da mensagem")
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)
        verbose_name = "Template de mensagem"
        verbose_name_plural = "Templates de mensagem"

    def __str__(self) -> str:
        return self.name


class MessageLog(models.Model):
    class Type(models.TextChoices):
        REMINDER = "reminder", "Lembrete"
        CHARGE = "charge", "Cobrança"
        INCOMING = "incoming", "Recebida"

    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"

    class Status(models.TextChoices):
        SUCCESS = "success", "Sucesso"
        FAILED = "failed", "Falha"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="message_logs")
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        related_name="logs",
        null=True,
        blank=True,
    )
    message_type = models.CharField("Tipo de mensagem", max_length=20, choices=Type.choices)
    channel = models.CharField("Canal", max_length=20, choices=Channel.choices)
    status = models.CharField("Status do envio", max_length=20, choices=Status.choices)
    sent_at = models.DateTimeField("Data envio", auto_now_add=True)
    payload = models.JSONField("Payload enviado", blank=True, null=True)
    response = models.JSONField("Resposta do provedor", blank=True, null=True)
    error_message = models.TextField("Mensagem de erro", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_logs",
    )

    class Meta:
        ordering = ("-sent_at",)
        verbose_name = "Log de envio"
        verbose_name_plural = "Logs de envio"

    def __str__(self) -> str:
        return f"{self.get_message_type_display()} - {self.client.name}"


class ClientInteraction(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="interactions")
    message_log = models.ForeignKey(
        MessageLog,
        on_delete=models.SET_NULL,
        related_name="interactions",
        null=True,
        blank=True,
    )
    received_at = models.DateTimeField("Data recebimento", auto_now_add=True)
    channel = models.CharField(
        "Canal",
        max_length=20,
        choices=MessageLog.Channel.choices,
        default=MessageLog.Channel.WHATSAPP,
    )
    raw_message = models.TextField("Mensagem recebida")
    normalized_option = models.CharField("Opção normalizada", max_length=50, blank=True)
    notes = models.TextField("Observações", blank=True)

    class Meta:
        ordering = ("-received_at",)
        verbose_name = "Interação do cliente"
        verbose_name_plural = "Interações dos clientes"

    def __str__(self) -> str:
        return f"{self.client.name} - {self.received_at:%d/%m/%Y %H:%M}"
