from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "monthly_fee", "due_date", "due_day", "status", "auto_messaging_enabled", "created_at")
    list_filter = ("status", "auto_messaging_enabled", "due_day", "due_date", "created_at")
    search_fields = ("name", "phone", "email")
    ordering = ("name",)
