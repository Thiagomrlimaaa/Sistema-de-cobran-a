#!/bin/sh

# Aplicar migrações (ignora erro se não houver banco configurado)
python manage.py migrate --noinput || echo "⚠️ Migrações não aplicadas (pode ser normal se não houver DATABASE_URL)"

# Criar superusuários (jeff e thiago com senha 1)
echo "👥 Criando superusuários..."
python manage.py create_users || echo "⚠️ Erro ao criar usuários (pode ser normal se não houver DATABASE_URL)"

# Iniciar bot em background
echo "🚀 Iniciando bot WhatsApp..."
cd /app/cobranca-bot
node index.js > /tmp/bot.log 2>&1 &
BOT_PID=$!
echo "✅ Bot iniciado com PID: $BOT_PID"

# Aguardar um pouco para o bot iniciar
sleep 3

# Verificar se bot está rodando
if ! kill -0 $BOT_PID 2>/dev/null; then
    echo "⚠️ Bot não está rodando, mas continuando com Django..."
else
    echo "✅ Bot está rodando"
fi

# Voltar para raiz e iniciar Django
cd /app
echo "🚀 Iniciando Django na porta 8000..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 cobranca_chatbot.wsgi:application

