from rest_framework import serializers

from clients.models import Client
from clients.serializers import ClientSerializer
from .models import ClientInteraction, MessageLog, MessageTemplate


class MessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageTemplate
        fields = [
            "id",
            "code",
            "name",
            "channel",
            "body",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MessageLogSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), source="client", write_only=True)

    class Meta:
        model = MessageLog
        fields = [
            "id",
            "client",
            "client_id",
            "template",
            "message_type",
            "channel",
            "status",
            "sent_at",
            "payload",
            "response",
            "error_message",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "client",
            "status",
            "sent_at",
            "response",
            "error_message",
            "created_by",
        ]


class ClientInteractionSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), source="client", write_only=True)

    class Meta:
        model = ClientInteraction
        fields = [
            "id",
            "client",
            "client_id",
            "message_log",
            "received_at",
            "channel",
            "raw_message",
            "normalized_option",
            "notes",
        ]
        read_only_fields = ["id", "client", "received_at"]

