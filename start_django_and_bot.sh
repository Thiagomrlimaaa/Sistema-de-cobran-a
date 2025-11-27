#!/bin/bash
# Script para rodar Django e Bot Node.js no mesmo serviço Render
# Isso permite rodar tudo no plano gratuito!

set -e

echo "🚀 Iniciando Django e Bot WhatsApp..."

# Iniciar bot Node.js em background
cd cobranca-bot
npm start &
BOT_PID=$!
cd ..

# Aguardar um pouco para o bot iniciar
sleep 5

# Iniciar Django (foreground - mantém o serviço ativo)
echo "✅ Bot iniciado (PID: $BOT_PID)"
echo "🌐 Iniciando Django..."
gunicorn cobranca_chatbot.wsgi:application --bind 0.0.0.0:$PORT

# Se o Django parar, parar o bot também
kill $BOT_PID 2>/dev/null || true

