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
    
    # Garantir que estamos no diretório correto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🚀 Iniciando Django e Bot WhatsApp...")
    print(f"📁 Diretório de trabalho: {os.getcwd()}")
    
    # Obter porta do ambiente (Render define PORT automaticamente)
    port = os.environ.get('PORT', '8000')
    
    # Iniciar bot Node.js em background
    print("📱 Iniciando bot WhatsApp...")
    bot_dir = os.path.join(script_dir, 'cobranca-bot')
    if os.path.exists(bot_dir):
        # Verificar se node_modules existe
        node_modules = os.path.join(bot_dir, 'node_modules')
        if not os.path.exists(node_modules):
            print("⚠️ node_modules não encontrado. Execute 'npm install' no diretório cobranca-bot primeiro.")
        else:
            bot_process = subprocess.Popen(
                ['npm', 'start'],
                cwd=bot_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print(f"✅ Bot iniciado (PID: {bot_process.pid})")
    else:
        print(f"⚠️ Diretório cobranca-bot não encontrado em {bot_dir}. Bot não será iniciado.")
    
    # Aguardar um pouco para o bot iniciar
    time.sleep(8)
    
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
        cwd=script_dir,  # Garantir que está no diretório correto
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

