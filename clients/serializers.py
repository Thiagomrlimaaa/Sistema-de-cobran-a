from rest_framework import serializers

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "monthly_fee",
            "due_date",
            "due_day",
            "payment_link",
            "status",
            "auto_messaging_enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "due_day", "created_at", "updated_at"]

