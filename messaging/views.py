from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
import requests
import time

from clients.models import Client
from .models import ClientInteraction, MessageLog, MessageTemplate
from .serializers import (
    ClientInteractionSerializer,
    MessageLogSerializer,
    MessageTemplateSerializer,
)
from .services import check_whatsapp_health, send_message_to_client


def _normalize_phone(phone: str) -> str:
    return "".join(filter(str.isdigit, phone or ""))


class MessageTemplateViewSet(viewsets.ModelViewSet):
    queryset = MessageTemplate.objects.all()
    serializer_class = MessageTemplateSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code", "body"]
    ordering_fields = ["code", "name", "channel", "created_at"]

    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        client_id = request.data.get("client_id")
        message_type = request.data.get("message_type")
        extra_context = request.data.get("extra_context", {})

        if not client_id or not message_type:
            return Response(
                {"detail": "client_id e message_type são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_types = {choice[0] for choice in MessageLog.Type.choices}
        if message_type not in valid_types:
            return Response(
                {"detail": f"message_type inválido. Use um dos valores: {', '.join(valid_types)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = Client.objects.filter(pk=client_id).first()
        if not client:
            return Response({"detail": "Cliente não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        template = self.get_object()
        message_log = send_message_to_client(
            client=client,
            template_code=template.code,
            message_type=message_type,
            extra_context=extra_context,
            initiated_by=request.user if request.user.is_authenticated else None,
        )
        serializer = MessageLogSerializer(message_log)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = MessageLog.objects.select_related("client", "template", "created_by")
    serializer_class = MessageLogSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["client__name", "client__phone", "template__name", "template__code"]
    ordering_fields = [
        "sent_at",
        "message_type",
        "status",
        "channel",
    ]

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        total_messages = queryset.count()
        successful_messages = queryset.filter(status=MessageLog.Status.SUCCESS).count()
        failed_messages = queryset.filter(status=MessageLog.Status.FAILED).count()
        clients_pending = Client.objects.filter(status=Client.Status.DELINQUENT).count()

        data = {
            "total_messages": total_messages,
            "successful_messages": successful_messages,
            "failed_messages": failed_messages,
            "success_rate": (successful_messages / total_messages) if total_messages else 0,
            "clients_pending": clients_pending,
        }
        return Response(data)


class ClientInteractionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = ClientInteraction.objects.select_related("client", "message_log")
    serializer_class = ClientInteractionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["client__name", "raw_message", "normalized_option"]
    ordering_fields = ["received_at", "channel"]


class WhatsAppWebhookView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "")
        if mode == "subscribe" and token == verify_token:
            return Response(data=challenge)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs):
        entries = request.data.get("entry", [])
        processed = 0

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    phone_raw = message.get("from")
                    message_body = message.get("text", {}).get("body", "")

                    if not phone_raw or not message_body:
                        continue

                    normalized_phone = _normalize_phone(phone_raw)
                    client = (
                        Client.objects.filter(phone__icontains=normalized_phone[-9:]).first()
                        if normalized_phone
                        else None
                    )
                    if not client:
                        continue

                    normalized_option = message_body.strip().split()[0]
                    interaction = ClientInteraction.objects.create(
                        client=client,
                        channel=MessageLog.Channel.WHATSAPP,
                        raw_message=message_body,
                        normalized_option=normalized_option,
                    )

                    if normalized_option == "1":
                        client.status = Client.Status.SETTLED
                        client.save(update_fields=["status"])
                    elif normalized_option == "2":
                        interaction.notes = "Cliente solicitou envio de comprovante."
                        interaction.save(update_fields=["notes"])
                    elif normalized_option == "3":
                        interaction.notes = "Cliente solicitou ajuda humana."
                        interaction.save(update_fields=["notes"])

                    processed += 1

        return Response({"processed": processed}, status=status.HTTP_200_OK)


class WhatsAppHealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            result = check_whatsapp_health()
        except Exception as exc:  # noqa: BLE001
            error_payload = {"error": str(exc), "provider": getattr(settings, "WHATSAPP_PROVIDER", "meta")}
            return Response(error_payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(result, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class BotControlView(APIView):
    """
    API para controlar o bot Node.js (WPPConnect).
    """
    permission_classes = [IsAuthenticated]

    def _get_bot_url(self, endpoint: str) -> str:
        bot_url = getattr(settings, "WPPCONNECT_BOT_URL", "http://localhost:3001")
        return f"{bot_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def get(self, request, *args, **kwargs):
        """Obter status do bot"""
        try:
            response = requests.get(self._get_bot_url("/status"), timeout=5)
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as exc:
            return Response(
                {"error": f"Não foi possível conectar ao bot: {str(exc)}", "status": "error"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def post(self, request, *args, **kwargs):
        """Iniciar ou parar o bot"""
        action_type = request.data.get("action", "start")  # start ou stop

        try:
            # Tentar conectar com retry (o bot pode estar iniciando)
            max_retries = 3
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    if action_type == "start":
                        response = requests.post(self._get_bot_url("/start"), timeout=30)
                    elif action_type == "stop":
                        response = requests.post(self._get_bot_url("/stop"), timeout=10)
                    else:
                        return Response(
                            {"error": "Ação inválida. Use 'start' ou 'stop'"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    response.raise_for_status()
                    return Response(response.json(), status=status.HTTP_200_OK)
                except requests.exceptions.ConnectionError as conn_exc:
                    last_exception = conn_exc
                    if attempt < max_retries - 1:
                        import time
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Tentativa {attempt + 1}/{max_retries} falhou ao conectar ao bot. Aguardando 3 segundos...")
                        time.sleep(3)
                    else:
                        # Última tentativa falhou
                        return Response(
                            {"error": f"Erro ao controlar bot: Não foi possível conectar ao bot na porta 3001. O bot pode estar iniciando ainda. Tente novamente em alguns segundos. Detalhes: {str(conn_exc)}"},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE,
                        )
                except requests.exceptions.RequestException as req_exc:
                    # Outros erros HTTP (não de conexão) - não fazer retry
                    return Response(
                        {"error": f"Erro ao controlar bot: {str(req_exc)}"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
            
            # Se chegou aqui, todas as tentativas falharam
            return Response(
                {"error": f"Erro ao controlar bot após {max_retries} tentativas: {str(last_exception)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            return Response(
                {"error": f"Erro inesperado ao controlar bot: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name='dispatch')
class BotQRCodeView(APIView):
    """Obter QR Code do bot"""
    permission_classes = [IsAuthenticated]

    def _get_bot_url(self, endpoint: str) -> str:
        bot_url = getattr(settings, "WPPCONNECT_BOT_URL", "http://localhost:3001")
        return f"{bot_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def get(self, request, *args, **kwargs):
        try:
            response = requests.get(self._get_bot_url("/qr"), timeout=5)
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as exc:
            return Response(
                {"error": f"Não foi possível conectar ao bot: {str(exc)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class BotSendBulkView(APIView):
    """Enviar mensagens em massa via bot"""
    permission_classes = [IsAuthenticated]

    def _get_bot_url(self, endpoint: str) -> str:
        bot_url = getattr(settings, "WPPCONNECT_BOT_URL", "http://localhost:3001")
        return f"{bot_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def post(self, request, *args, **kwargs):
        clients_ids = request.data.get("client_ids", [])
        message = request.data.get("message", "")

        if not clients_ids or not message:
            return Response(
                {"error": "client_ids e message são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar se o bot está conectado antes de tentar enviar
        try:
            status_response = requests.get(self._get_bot_url("/status"), timeout=5)
            status_response.raise_for_status()
            bot_status = status_response.json()
            
            if bot_status.get("status") != "connected" or not bot_status.get("isConnected"):
                return Response(
                    {"error": "Bot não está conectado. Conecte o bot antes de enviar mensagens."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        except requests.exceptions.RequestException as exc:
            return Response(
                {"error": f"Não foi possível verificar o status do bot: {str(exc)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Buscar clientes PRIMEIRO
        clients = Client.objects.filter(id__in=clients_ids)
        if not clients.exists():
            return Response(
                {"error": "Nenhum cliente encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Sincronizar contatos antes de enviar (verificar se existem no WhatsApp)
        # IMPORTANTE: Não bloquear envio se sincronização falhar
        try:
            contacts_to_sync = [
                {"phone": client.formatted_phone, "name": client.name}
                for client in clients
            ]
            # Fazer sincronização em background (não esperar)
            sync_response = requests.post(
                self._get_bot_url("/sync-contacts"),
                json={"contacts": contacts_to_sync},
                timeout=10,  # Timeout curto - não bloquear envio
            )
            if sync_response.status_code == 200:
                sync_result = sync_response.json()
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Contatos sincronizados: {sync_result.get('verified', 0)} verificados, {sync_result.get('not_found', 0)} não encontrados")
        except requests.exceptions.RequestException as sync_error:
            # Se falhar a sincronização, continua mesmo assim (não é crítico)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Sincronização de contatos falhou (não crítico): {str(sync_error)}")
            # Continuar com o envio mesmo se sincronização falhar

        # Preparar lista de telefones e renderizar mensagem para cada cliente
        from calendar import monthrange
        from datetime import date as date_class
        
        clients_data = []
        today = timezone.localdate()
        
        for client in clients:
            # Renderizar mensagem com variáveis do cliente
            rendered_message = message
            try:
                # Calcular data de vencimento
                due_date = None
                if client.due_date:
                    due_date = client.due_date
                    # Se a data já passou, calcular próxima ocorrência
                    if due_date < today:
                        if due_date.month == 12:
                            next_year = due_date.year + 1
                            next_month = 1
                        else:
                            next_year = due_date.year
                            next_month = due_date.month + 1
                        days_in_month = monthrange(next_year, next_month)[1]
                        next_day = min(due_date.day, days_in_month)
                        due_date = date_class(next_year, next_month, next_day)
                elif hasattr(client, 'due_day') and client.due_day:
                    # Usar due_day para calcular próxima data
                    day = client.due_day
                    if today.day >= day:
                        # Já passou este mês
                        if today.month == 12:
                            next_year = today.year + 1
                            next_month = 1
                        else:
                            next_year = today.year
                            next_month = today.month + 1
                    else:
                        # Ainda não passou este mês
                        next_year = today.year
                        next_month = today.month
                    
                    days_in_month = monthrange(next_year, next_month)[1]
                    next_day = min(day, days_in_month)
                    due_date = date_class(next_year, next_month, next_day)
                else:
                    # Se não tem data, usar data de hoje como fallback
                    due_date = today
                
                # Substituir variáveis na mensagem - múltiplas tags para nome
                client_name = client.name or ""
                rendered_message = rendered_message.replace("{{nome}}", client_name)
                rendered_message = rendered_message.replace("{{nome_cliente}}", client_name)
                rendered_message = rendered_message.replace("{{cliente}}", client_name)
                
                # Formatar valor em reais
                try:
                    valor_str = f"{client.monthly_fee:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except (AttributeError, TypeError):
                    valor_str = "0,00"
                rendered_message = rendered_message.replace("{{valor}}", valor_str)
                
                # Substituir data de vencimento
                if due_date:
                    rendered_message = rendered_message.replace("{{vencimento}}", due_date.strftime("%d/%m/%Y"))
                else:
                    rendered_message = rendered_message.replace("{{vencimento}}", "Não definido")
                
                # Substituir "vence hoje" pela data correta
                if due_date and due_date == today:
                    # Se vence hoje, manter "vence hoje"
                    rendered_message = rendered_message.replace("vence hoje", "vence hoje")
                elif due_date:
                    # Se não vence hoje, substituir pela data
                    rendered_message = rendered_message.replace("vence hoje", f"vence em {due_date.strftime('%d/%m/%Y')}")
                
                # Substituir link de pagamento
                rendered_message = rendered_message.replace("{{link_pagamento}}", client.payment_link or "")
            except Exception as e:
                # Se houver erro na renderização, usa a mensagem original
                import logging
                logger = logging.getLogger(__name__)
                logger.exception(f"Erro ao renderizar mensagem para {client.name}: {e}")
                rendered_message = message
            
            # Validar telefone antes de adicionar
            phone = client.formatted_phone
            phone_digits = "".join(filter(str.isdigit, phone or ""))
            if not phone or len(phone_digits) < 10:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Telefone inválido para cliente {client.name}: {phone}")
                continue
            
            clients_data.append({
                "phone": phone,
                "message": rendered_message
            })

        try:
            # Enviar uma mensagem por vez para melhor controle
            results = []
            errors = []
            
            for idx, client_data in enumerate(clients_data):
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Enviando mensagem {idx + 1}/{len(clients_data)} para {client_data['phone']}")
                    
                    response = requests.post(
                        self._get_bot_url("/send"),
                        json={"phone": client_data["phone"], "message": client_data["message"]},
                        timeout=30,
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get("success"):
                        results.append({"phone": client_data["phone"], "success": True})
                        logger.info(f"✅ Mensagem enviada com sucesso para {client_data['phone']}")
                    else:
                        error_msg = result.get("error", "Erro desconhecido")
                        errors.append({"phone": client_data["phone"], "error": error_msg})
                        logger.error(f"❌ Erro ao enviar para {client_data['phone']}: {error_msg}")
                except requests.exceptions.RequestException as exc:
                    error_msg = str(exc)
                    errors.append({"phone": client_data["phone"], "error": error_msg})
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"❌ Erro de conexão ao enviar para {client_data['phone']}: {error_msg}")
                
                # Delay entre envios (2 segundos) - exceto no último
                if idx < len(clients_data) - 1:
                    time.sleep(2)
            
            # Criar logs de mensagens
            for client in clients:
                try:
                    client_success = any(
                        r.get("phone") == client.formatted_phone and r.get("success")
                        for r in results
                    )
                    MessageLog.objects.create(
                        client=client,
                        message_type=MessageLog.Type.CHARGE,
                        channel=MessageLog.Channel.WHATSAPP,
                        status=MessageLog.Status.SUCCESS if client_success else MessageLog.Status.FAILED,
                        payload={"message": message, "bulk_send": True},
                        response={"success": client_success},
                        created_by=request.user,
                    )
                except Exception as log_error:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erro ao criar log para cliente {client.name}: {log_error}")

            result = {
                "success": True,
                "sent": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors,
            }

            return Response(result, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Erro ao enviar mensagens via bot")
            return Response(
                {"error": f"Erro ao enviar mensagens: {str(exc)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Erro inesperado ao enviar mensagens em massa")
            return Response(
                {"error": f"Erro inesperado: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WPPConnectWebhookView(APIView):
    """
    Webhook para receber mensagens do bot Node.js (wppconnect).
    """
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone = request.data.get("phone", "").strip()
        message = request.data.get("message", "").strip()
        message_type = request.data.get("message_type", "chat").strip()

        # Validar dados obrigatórios (message pode ser vazio se for imagem)
        if not phone:
            return Response(
                {"error": "phone é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Se for imagem/documento, tratar como comprovante
        if message_type in ["image", "document"] or message == "[COMPROVANTE_ENVIADO]":
            return self._process_receipt(phone, request)

        # Ignorar mensagens de status/broadcast
        if "status@broadcast" in phone or "@broadcast" in phone:
            return Response(
                {"error": "Mensagem de broadcast ignorada"},
                status=status.HTTP_200_OK,  # Retorna 200 para não gerar erro no bot
            )

        # Validar telefone (deve ter pelo menos 10 dígitos)
        phone_digits = "".join(filter(str.isdigit, phone))
        if len(phone_digits) < 10:
            return Response(
                {"error": "Telefone inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Processar mensagem normalmente (só chega aqui se não for imagem)
        if not message:
            return Response(
                {"error": "message é obrigatório para mensagens de texto"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._process_message(phone, message, request)

    def _process_message(self, phone: str, message: str, request) -> Response:
        """Processa uma mensagem recebida do WhatsApp"""
        # Normalizar telefone
        normalized_phone = _normalize_phone(phone)
        if not normalized_phone or len(normalized_phone) < 9:
            return Response(
                {"error": "Telefone inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Buscar cliente pelo telefone (busca pelos últimos 9 dígitos)
        client = Client.objects.filter(phone__icontains=normalized_phone[-9:]).first()

        # Se não encontrou cliente, retornar mensagem genérica
        if not client:
            return Response(
                {
                    "processed": False,
                    "auto_reply": (
                        "Olá! Não encontramos seu cadastro em nosso sistema.\n"
                        "Por favor, entre em contato conosco através dos nossos canais oficiais."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        # Criar interação
        normalized_option = message.strip().split()[0] if message.strip() else ""
        interaction = ClientInteraction.objects.create(
            client=client,
            channel=MessageLog.Channel.WHATSAPP,
            raw_message=message,
            normalized_option=normalized_option,
        )

        # Processar ações baseadas em opções numéricas
        if normalized_option == "1":
            interaction.notes = "Cliente solicitou falar com atendente."
            interaction.save(update_fields=["notes"])
        elif normalized_option == "2":
            interaction.notes = "Cliente solicitou enviar comprovante."
            interaction.save(update_fields=["notes"])

        # Gerar resposta automática
        auto_reply = self._generate_auto_reply(client, message)

        # Criar log da mensagem recebida
        MessageLog.objects.create(
            client=client,
            message_type=MessageLog.Type.INCOMING,
            channel=MessageLog.Channel.WHATSAPP,
            status=MessageLog.Status.SUCCESS,
            payload={"phone": phone, "message": message},
        )

        return Response({
            "processed": True,
            "client_id": client.id,
            "client_name": client.name,
            "auto_reply": auto_reply,
            "interaction_id": interaction.id,
        }, status=status.HTTP_200_OK)

    def _process_receipt(self, phone: str, request) -> Response:
        """Processa comprovante de pagamento enviado pelo cliente"""
        normalized_phone = _normalize_phone(phone)
        if not normalized_phone or len(normalized_phone) < 9:
            return Response(
                {"error": "Telefone inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Buscar cliente pelo telefone
        client = Client.objects.filter(phone__icontains=normalized_phone[-9:]).first()
        
        if not client:
            return Response(
                {
                    "processed": False,
                    "auto_reply": "Não encontramos seu cadastro. Entre em contato conosco.",
                },
                status=status.HTTP_200_OK,
            )
        
        # Marcar como quitado e criar interação
        client.status = Client.Status.SETTLED
        client.save(update_fields=["status"])
        
        interaction = ClientInteraction.objects.create(
            client=client,
            channel=MessageLog.Channel.WHATSAPP,
            raw_message="[COMPROVANTE_ENVIADO]",
            normalized_option="2",
            notes="Cliente enviou comprovante de pagamento. Status atualizado automaticamente.",
        )
        
        # Criar log
        MessageLog.objects.create(
            client=client,
            message_type=MessageLog.Type.INCOMING,
            channel=MessageLog.Channel.WHATSAPP,
            status=MessageLog.Status.SUCCESS,
            payload={"phone": phone, "message": "[COMPROVANTE_ENVIADO]", "type": "image"},
        )
        
        return Response({
            "processed": True,
            "client_id": client.id,
            "client_name": client.name,
            "auto_reply": "✅ Comprovante recebido! Seu pagamento foi registrado e seu status foi atualizado.",
            "interaction_id": interaction.id,
        }, status=status.HTTP_200_OK)

    def _generate_auto_reply(self, client: Client, message: str) -> str | None:
        """
        Gera resposta automática baseada na mensagem do cliente.
        Apenas responde se a mensagem for exatamente "1" ou "2" para evitar flood.
        """
        # Remover espaços e verificar se é apenas um número
        message_clean = message.strip()
        
        # Verificar se a mensagem é APENAS "1" ou "2" (sem outros caracteres)
        if message_clean == "1":
            return (
                "👤 Nossa equipe entrará em contato em breve!\n"
                "Aguarde que um atendente irá te responder."
            )
        
        if message_clean == "2":
            return (
                "📄 Para enviar seu comprovante:\n"
                "Envie a imagem do comprovante aqui mesmo.\n"
                "Nossa equipe analisará e atualizará seu status em breve!"
            )
        
        # Se não for "1" ou "2", não retorna resposta automática (evita flood)
        return None
