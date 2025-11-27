#!/bin/sh

# Aplicar migrações (ignora erro se não houver banco configurado)
python manage.py migrate --noinput || echo "⚠️ Migrações não aplicadas (pode ser normal se não houver DATABASE_URL)"

# Criar superusuários (jeff e thiago com senha 1)
echo "👥 Criando superusuários..."
python manage.py create_users || echo "⚠️ Erro ao criar usuários (pode ser normal se não houver DATABASE_URL)"

# Iniciar Django (bot roda em app separado no Koyeb)
echo "🚀 Iniciando Django na porta 8000..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 cobranca_chatbot.wsgi:application

