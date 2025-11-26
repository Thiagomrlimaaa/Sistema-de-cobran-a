from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import requests
import logging

from .models import Client

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Client)
def sync_client_to_whatsapp(sender, instance, created, **kwargs):
    """
    Sincroniza o cliente com o WhatsApp quando criado ou atualizado
    """
    # Só sincronizar se o telefone mudou ou é um novo cliente
    if not instance.phone or not instance.auto_messaging_enabled:
        return
    
    try:
        bot_url = getattr(settings, "WPPCONNECT_BOT_URL", "http://localhost:3001")
        
        # Verificar se o bot está conectado
        try:
            status_response = requests.get(f"{bot_url}/status", timeout=5)
            if status_response.status_code == 200:
                bot_status = status_response.json()
                if bot_status.get("status") != "connected":
                    logger.info(f"Bot não está conectado, pulando sincronização de {instance.name}")
                    return
            else:
                return
        except requests.exceptions.RequestException:
            logger.warning("Não foi possível verificar status do bot, pulando sincronização")
            return
        
        # Adicionar contato ao WhatsApp
        try:
            response = requests.post(
                f"{bot_url}/add-contact",
                json={
                    "phone": instance.formatted_phone,
                    "name": instance.name,
                },
                timeout=10,
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("exists"):
                    logger.info(f"✅ Cliente {instance.name} ({instance.formatted_phone}) verificado no WhatsApp")
                else:
                    logger.warning(f"⚠️ Cliente {instance.name} ({instance.formatted_phone}) não encontrado no WhatsApp")
            else:
                logger.warning(f"Erro ao sincronizar cliente {instance.name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao sincronizar cliente {instance.name} com WhatsApp: {e}")
    except Exception as e:
        logger.exception(f"Erro inesperado ao sincronizar cliente {instance.name}: {e}")

