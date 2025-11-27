"""
Serviço Python para gerenciar o bot WhatsApp.
Substitui o bot Node.js, rodando dentro do Django.
"""
import threading
import time
import base64
import io
from typing import Optional, Dict, Any
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Estado global do bot
_bot_state = {
    'status': 'disconnected',  # disconnected, connecting, connected, error
    'qr_code': None,
    'error': None,
    'connected_at': None,
    'client': None,
    'thread': None,
}

try:
    from whatsapp_web import WhatsApp
    
    WHATSAPP_AVAILABLE = True
except ImportError:
    WHATSAPP_AVAILABLE = False
    logger.warning("whatsapp-web.py não está instalado. Instale com: pip install whatsapp-web.py")


def get_bot_status() -> Dict[str, Any]:
    """Retorna o status atual do bot"""
    return {
        'status': _bot_state['status'],
        'isConnected': _bot_state['status'] == 'connected',
        'qrCode': _bot_state['qr_code'],
        'error': _bot_state['error'],
        'connectedAt': _bot_state['connected_at'],
    }


def get_qr_code() -> Optional[str]:
    """Retorna o QR Code atual (base64)"""
    return _bot_state['qr_code']


def start_bot() -> Dict[str, Any]:
    """Inicia o bot WhatsApp em uma thread separada"""
    if not WHATSAPP_AVAILABLE:
        _bot_state['status'] = 'error'
        _bot_state['error'] = 'whatsapp-web.py não está instalado'
        return {
            'success': False,
            'error': 'Biblioteca whatsapp-web.py não está instalada. Execute: pip install whatsapp-web.py'
        }
    
    if _bot_state['status'] == 'connected':
        return {
            'success': True,
            'message': 'Bot já está conectado',
            'status': _bot_state['status'],
            'qrCode': None,
        }
    
    if _bot_state['status'] in ['connecting', 'waiting_qr']:
        return {
            'success': True,
            'message': 'Bot já está inicializando',
            'status': _bot_state['status'],
            'qrCode': _bot_state['qr_code'],
        }
    
    # Iniciar em thread separada
    if _bot_state['thread'] is None or not _bot_state['thread'].is_alive():
        _bot_state['status'] = 'connecting'
        _bot_state['error'] = None
        _bot_state['thread'] = threading.Thread(target=_run_bot, daemon=True)
        _bot_state['thread'].start()
    
    # Aguardar um pouco para o QR Code ser gerado
    time.sleep(2)
    
    return {
        'success': True,
        'message': 'Bot iniciado com sucesso',
        'status': _bot_state['status'],
        'qrCode': _bot_state['qr_code'],
    }


def stop_bot() -> Dict[str, Any]:
    """Para o bot WhatsApp"""
    if _bot_state['client']:
        try:
            _bot_state['client'].close()
        except:
            pass
    
    _bot_state['client'] = None
    _bot_state['status'] = 'disconnected'
    _bot_state['qr_code'] = None
    _bot_state['connected_at'] = None
    _bot_state['error'] = None
    
    return {
        'success': True,
        'message': 'Bot parado com sucesso',
        'status': _bot_state['status'],
    }


def send_message(phone: str, message: str) -> Dict[str, Any]:
    """Envia uma mensagem via WhatsApp"""
    if _bot_state['status'] != 'connected' or not _bot_state['client']:
        return {
            'success': False,
            'error': 'Bot não está conectado. Conecte o bot antes de enviar mensagens.',
        }
    
    try:
        # Formatar telefone (remover caracteres não numéricos e adicionar @c.us)
        phone_clean = ''.join(filter(str.isdigit, phone))
        if not phone_clean:
            return {
                'success': False,
                'error': 'Telefone inválido',
            }
        
        phone_formatted = f"{phone_clean}@c.us"
        
        # Enviar mensagem
        _bot_state['client'].send_message(phone_formatted, message)
        
        return {
            'success': True,
            'message': 'Mensagem enviada com sucesso',
        }
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }


def _run_bot():
    """Função que roda o bot em background"""
    global _bot_state
    
    try:
        _bot_state['status'] = 'waiting_qr'
        logger.info("Iniciando bot WhatsApp...")
        
        # Criar instância do WhatsApp
        # whatsapp-web.py usa selenium, então precisa de Chrome/Chromium
        whatsapp = WhatsApp()
        
        # Callback para QR Code
        def on_qr_code(qr_code):
            """Callback quando QR Code é gerado"""
            try:
                # Converter QR Code para base64
                if hasattr(qr_code, 'read'):
                    qr_bytes = qr_code.read()
                else:
                    qr_bytes = qr_code
                
                qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
                _bot_state['qr_code'] = qr_base64
                logger.info("QR Code gerado")
            except Exception as e:
                logger.error(f"Erro ao processar QR Code: {str(e)}")
        
        # Conectar
        whatsapp.connect(on_qr_code=on_qr_code)
        
        _bot_state['client'] = whatsapp
        _bot_state['status'] = 'connected'
        _bot_state['connected_at'] = time.time()
        _bot_state['error'] = None
        logger.info("Bot WhatsApp conectado com sucesso!")
        
        # Manter conexão ativa
        while _bot_state['status'] == 'connected':
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Erro ao executar bot: {str(e)}")
        _bot_state['status'] = 'error'
        _bot_state['error'] = str(e)
        _bot_state['client'] = None

