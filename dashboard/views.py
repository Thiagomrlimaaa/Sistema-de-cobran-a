from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from clients.models import Client
from messaging.models import MessageLog, MessageTemplate

from .forms import ClientForm, ContactImportForm


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        tomorrow = today + timezone.timedelta(days=1)

        clients = Client.objects.all()
        context.update(
            {
                "total_clients": clients.count(),
                "active_clients": clients.filter(status=Client.Status.ACTIVE).count(),
                "delinquent_clients": clients.filter(status=Client.Status.DELINQUENT).count(),
                "due_today": clients.filter(due_date=today).count(),
                "due_tomorrow": clients.filter(due_date=tomorrow).count(),
                "monthly_revenue": clients.aggregate(total=Sum("monthly_fee"))["total"] or 0,
                "last_logs": MessageLog.objects.select_related("client", "template")
                .order_by("-sent_at")[:10],
            }
        )
        return context


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "dashboard/client_list.html"
    paginate_by = 20
    context_object_name = "clients"

    def get_queryset(self):
        queryset = Client.objects.all().order_by("name")
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["statuses"] = Client.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_query"] = self.request.GET.get("q", "")
        context["templates"] = MessageTemplate.objects.filter(is_active=True, channel=MessageTemplate.Channel.WHATSAPP)
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "dashboard/client_form.html"
    success_url = reverse_lazy("dashboard:clients")

    def form_valid(self, form: ClientForm) -> HttpResponse:
        messages.success(self.request, "Cliente criado com sucesso.")
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "dashboard/client_form.html"
    success_url = reverse_lazy("dashboard:clients")

    def form_valid(self, form: ClientForm) -> HttpResponse:
        messages.success(self.request, "Cliente atualizado com sucesso.")
        return super().form_valid(form)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = "dashboard/client_confirm_delete.html"
    success_url = reverse_lazy("dashboard:clients")

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Cliente removido com sucesso.")
        return super().delete(request, *args, **kwargs)


class ContactImportView(LoginRequiredMixin, FormView):
    form_class = ContactImportForm
    template_name = "dashboard/contact_import.html"

    def form_valid(self, form: ContactImportForm) -> HttpResponse:
        uploaded = form.cleaned_data["file"]
        rows = getattr(uploaded, "parsed_rows", [])
        created = 0
        updated = 0

        for row in rows:
            phone_digits = "".join(filter(str.isdigit, row["phone"]))
            lookup = {}
            if len(phone_digits) >= 9:
                lookup["phone__icontains"] = phone_digits[-9:]
            else:
                lookup["phone__icontains"] = phone_digits

            existing = Client.objects.filter(**lookup).first()
            status = row["status"] if row["status"] in Client.Status.values else Client.Status.ACTIVE

            if existing:
                for field, value in (
                    ("name", row["name"]),
                    ("phone", row["phone"]),
                    ("email", row["email"]),
                    ("monthly_fee", row["monthly_fee"]),
                    ("due_date", row["due_date"]),
                    ("payment_link", row["payment_link"]),
                    ("status", status),
                ):
                    setattr(existing, field, value)
                existing.save()
                updated += 1
            else:
                Client.objects.create(
                    name=row["name"],
                    phone=row["phone"],
                    email=row["email"],
                    monthly_fee=row["monthly_fee"],
                    due_date=row["due_date"],
                    payment_link=row["payment_link"],
                    status=status,
                )
                created += 1

        messages.success(
            self.request,
            f"Importação concluída. Criados: {created}, atualizados: {updated}.",
        )
        return redirect(reverse("dashboard:clients"))


class TriggerMessageView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        client_id = request.POST.get("client_id")
        template_code = request.POST.get("template_code")
        if not client_id or not template_code:
            messages.error(request, "Cliente ou template inválidos.")
            return redirect(request.META.get("HTTP_REFERER", reverse("dashboard:clients")))

        client = Client.objects.filter(id=client_id).first()
        if not client:
            messages.error(request, "Cliente não encontrado.")
            return redirect(request.META.get("HTTP_REFERER", reverse("dashboard:clients")))

        template = MessageTemplate.objects.filter(code=template_code, is_active=True).first()
        if not template:
            messages.error(request, "Template não encontrado ou inativo.")
            return redirect(request.META.get("HTTP_REFERER", reverse("dashboard:clients")))

        from messaging.services import send_message_to_client  # import local para evitar ciclos

        try:
            message_type = (
                MessageLog.Type.CHARGE if template_code == MessageLog.Type.CHARGE else MessageLog.Type.REMINDER
            )
            send_message_to_client(
                client=client,
                template_code=template.code,
                message_type=message_type,
                initiated_by=request.user,
            )
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Falha ao enviar mensagem: {exc}")
        else:
            messages.success(request, "Mensagem enviada com sucesso.")
        return redirect(request.META.get("HTTP_REFERER", reverse("dashboard:clients")))


class BotControlView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/bot_control.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        from calendar import monthrange
        from datetime import date, timedelta
        
        context = super().get_context_data(**kwargs)
        
        # Filtrar por data de vencimento e veículo se fornecido
        filter_date = self.request.GET.get("filter_date", "").strip()
        filter_day = self.request.GET.get("filter_day", "").strip()
        filter_vehicle = self.request.GET.get("filter_vehicle", "").strip()
        
        queryset = Client.objects.filter(auto_messaging_enabled=True)
        
        # Filtrar por tipo de veículo
        if filter_vehicle and filter_vehicle in [Client.VehicleType.MOTO, Client.VehicleType.CARRO]:
            queryset = queryset.filter(vehicle_type=filter_vehicle)
        
        if filter_date:
            try:
                # Converter data do formato DD/MM/YYYY
                day, month, year = map(int, filter_date.split("/"))
                filter_date_obj = date(year, month, day)
                today = timezone.localdate()
                
                # Se a data já passou, calcular próxima ocorrência
                if filter_date_obj < today:
                    # Calcular próximo mês/ano
                    if month == 12:
                        next_year = year + 1
                        next_month = 1
                    else:
                        next_year = year
                        next_month = month + 1
                    
                    # Garantir que o dia existe no próximo mês
                    days_in_month = monthrange(next_year, next_month)[1]
                    next_day = min(day, days_in_month)
                    filter_date_obj = date(next_year, next_month, next_day)
                
                # Filtrar clientes com vencimento na data calculada
                # Busca clientes que têm vencimento neste dia específico
                queryset = queryset.filter(
                    Q(due_date=filter_date_obj) | 
                    Q(due_date__isnull=True, due_day=filter_date_obj.day) |
                    Q(due_date__day=filter_date_obj.day, due_date__month=filter_date_obj.month, due_date__year=filter_date_obj.year)
                )
            except (ValueError, AttributeError):
                pass  # Se data inválida, não filtrar
        elif filter_day:
            try:
                day = int(filter_day)
                today = timezone.localdate()
                
                # Filtrar clientes que têm vencimento neste dia do mês
                # Busca por due_day (dia do mês) independente do mês/ano
                queryset = queryset.filter(due_day=day)
                
                # Opcional: também filtrar por due_date se quiser ser mais específico
                # Mas por enquanto, filtra apenas por due_day para pegar todos do dia
            except ValueError:
                pass  # Se dia inválido, não filtrar
        
        context["clients"] = queryset.order_by("name")
        context["filter_date"] = filter_date
        context["filter_day"] = filter_day
        context["filter_vehicle"] = filter_vehicle
        return context