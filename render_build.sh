#!/bin/bash
# Script de build para Render.com
# Instala dependências, aplica migrações, coleta arquivos estáticos e cria usuários

set -e  # Para na primeira erro

echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "🗄️ Aplicando migrações..."
python manage.py migrate --noinput

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || echo "⚠️ Aviso: collectstatic falhou (pode ser normal se não houver arquivos estáticos)"

echo "👥 Criando usuários..."
python manage.py create_users

echo "✅ Build concluído com sucesso!"

