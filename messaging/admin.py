from django.contrib import admin

from .models import ClientInteraction, MessageLog, MessageTemplate


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "channel", "is_active", "updated_at")
    list_filter = ("channel", "is_active", "created_at")
    search_fields = ("code", "name", "body")
    ordering = ("code",)


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ("client", "message_type", "channel", "status", "sent_at")
    list_filter = ("message_type", "channel", "status", "sent_at")
    search_fields = ("client__name", "client__phone", "template__code", "template__name")
    readonly_fields = ("payload", "response", "error_message", "sent_at")


@admin.register(ClientInteraction)
class ClientInteractionAdmin(admin.ModelAdmin):
    list_display = ("client", "channel", "normalized_option", "received_at")
    list_filter = ("channel", "normalized_option", "received_at")
    search_fields = ("client__name", "raw_message")
