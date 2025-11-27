#!/usr/bin/env python
"""
Script para iniciar Django e Bot Node.js no mesmo processo.
Permite rodar tudo no plano gratuito do Render sem precisar de Background Worker.
"""
import subprocess
import sys
import os
import signal
import time

# Processos
django_process = None
bot_process = None


def signal_handler(sig, frame):
    """Lidar com sinais de parada (Ctrl+C, etc)"""
    print("\n🛑 Parando servidores...")
    if bot_process:
        bot_process.terminate()
    if django_process:
        django_process.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    global django_process, bot_process
    
    print("🚀 Iniciando Django e Bot WhatsApp...")
    
    # Obter porta do ambiente (Render define PORT automaticamente)
    port = os.environ.get('PORT', '8000')
    
    # Iniciar bot Node.js em background
    print("📱 Iniciando bot WhatsApp...")
    bot_dir = os.path.join(os.path.dirname(__file__), 'cobranca-bot')
    if os.path.exists(bot_dir):
        bot_process = subprocess.Popen(
            ['npm', 'start'],
            cwd=bot_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✅ Bot iniciado (PID: {bot_process.pid})")
    else:
        print("⚠️ Diretório cobranca-bot não encontrado. Bot não será iniciado.")
    
    # Aguardar um pouco para o bot iniciar
    time.sleep(5)
    
    # Iniciar Django (foreground - mantém o serviço ativo)
    print(f"🌐 Iniciando Django na porta {port}...")
    django_process = subprocess.Popen(
        [
            'gunicorn',
            'cobranca_chatbot.wsgi:application',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '2',
            '--timeout', '120',
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    
    print(f"✅ Django iniciado (PID: {django_process.pid})")
    print("🎉 Servidores rodando! Pressione Ctrl+C para parar.")
    
    # Aguardar Django terminar (ou erro)
    try:
        django_process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        # Se Django parar, parar o bot também
        if bot_process:
            print("🛑 Parando bot...")
            bot_process.terminate()
            bot_process.wait()


if __name__ == '__main__':
    main()

