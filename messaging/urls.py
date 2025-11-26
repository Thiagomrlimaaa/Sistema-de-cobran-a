from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BotControlView,
    BotQRCodeView,
    BotSendBulkView,
    ClientInteractionViewSet,
    MessageLogViewSet,
    MessageTemplateViewSet,
    WhatsAppHealthView,
    WhatsAppWebhookView,
    WPPConnectWebhookView,
)

router = DefaultRouter()
router.register(r"message-templates", MessageTemplateViewSet, basename="message-template")
router.register(r"message-logs", MessageLogViewSet, basename="message-log")
router.register(r"client-interactions", ClientInteractionViewSet, basename="client-interaction")

urlpatterns = router.urls + [
    path("webhooks/whatsapp/", WhatsAppWebhookView.as_view(), name="whatsapp-webhook"),
    path("webhooks/whatsapp/wppconnect/", WPPConnectWebhookView.as_view(), name="wppconnect-webhook"),
    path("integrations/whatsapp/health/", WhatsAppHealthView.as_view(), name="whatsapp-health"),
    path("bot/control/", BotControlView.as_view(), name="bot-control"),
    path("bot/qr/", BotQRCodeView.as_view(), name="bot-qr"),
    path("bot/send-bulk/", BotSendBulkView.as_view(), name="bot-send-bulk"),
]

