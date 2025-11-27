#!/bin/bash
# Script para iniciar Django e Bot simultaneamente

# Iniciar bot em background na porta 3001
# Railway usa PORT para o serviço principal (Django), então o bot usa porta fixa 3001
cd /code/cobranca-bot

# Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    echo "Instalando dependências do bot..."
    npm install
fi

# Configurar variáveis de ambiente do bot
export BOT_PORT=3001
export DJANGO_API_URL=${DJANGO_API_URL:-"http://localhost:${PORT:-8000}/api"}
export WHATSAPP_SESSION=${WHATSAPP_SESSION:-"cobranca"}
export PUPPETEER_EXECUTABLE_PATH=${PUPPETEER_EXECUTABLE_PATH:-"/usr/bin/chromium-browser"}
export CHROMIUM_PATH=${CHROMIUM_PATH:-"/usr/bin/chromium-browser"}
export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
# Railway usa PORT para o serviço principal, então não desabilitamos

echo "Iniciando bot na porta 3001..."
# Limpar logs anteriores
echo "" > /tmp/bot.log
npm start >> /tmp/bot.log 2>&1 &
BOT_PID=$!
echo "Bot iniciado com PID: $BOT_PID"

# Aguardar bot iniciar e verificar se está rodando
echo "Aguardando bot iniciar..."
MAX_RETRIES=30
RETRY_COUNT=0
BOT_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Verificar se processo ainda está rodando
    if ! kill -0 $BOT_PID 2>/dev/null; then
        echo "❌ ERRO: Bot não está mais rodando (PID: $BOT_PID)"
        echo "Logs do bot:"
        cat /tmp/bot.log 2>/dev/null || echo "Nenhum log disponível"
        echo ""
        echo "Tentando reiniciar bot..."
        cd /code/cobranca-bot
        npm start > /tmp/bot.log 2>&1 &
        BOT_PID=$!
        RETRY_COUNT=0
        sleep 5
        continue
    fi
    
    # Verificar se bot está respondendo
    if curl -s http://localhost:3001/status > /dev/null 2>&1; then
        echo "✅ Bot está respondendo na porta 3001"
        BOT_READY=true
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ Aguardando bot responder... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ "$BOT_READY" = false ]; then
    echo "⚠️ Bot não está respondendo após $MAX_RETRIES tentativas"
    echo "Logs do bot:"
    tail -n 50 /tmp/bot.log 2>/dev/null || echo "Nenhum log disponível"
    echo ""
    echo "Continuando com Django mesmo assim..."
    echo "O bot pode estar iniciando ainda - tente novamente em alguns segundos"
else
    echo "✅ Bot iniciado e pronto!"
fi

# Iniciar Django na porta definida pelo Railway (ou 8000 como padrão)
# IMPORTANTE: Django deve ser o processo principal (não usar &)
cd /code
DJANGO_PORT=${PORT:-8000}
echo "Iniciando Django na porta ${DJANGO_PORT}..."
exec gunicorn --bind 0.0.0.0:${DJANGO_PORT} --workers 2 --timeout 120 cobranca_chatbot.wsgi
