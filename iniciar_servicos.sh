#!/bin/bash
# Script para iniciar Django e Bot no Oracle Cloud
# Execute este script após configurar o projeto

echo "=========================================="
echo "  Iniciando Serviços"
echo "=========================================="

# Ativar ambiente virtual e iniciar Django
cd ~/projetos/chatbot-cobranca
source venv/bin/activate

echo "[1/2] Iniciando Django..."
pm2 start "python manage.py runserver 0.0.0.0:8000" --name django --interpreter python3.11

# Iniciar Bot
cd ~/projetos/chatbot-cobranca/cobranca-bot
echo "[2/2] Iniciando Bot WhatsApp..."
pm2 start "npm start" --name whatsapp-bot

# Salvar configuração
pm2 save

echo ""
echo "=========================================="
echo "  Serviços Iniciados!"
echo "=========================================="
echo ""
echo "Status:"
pm2 status
echo ""
echo "Para ver logs:"
echo "  pm2 logs django"
echo "  pm2 logs whatsapp-bot"
echo ""
echo "Para reiniciar:"
echo "  pm2 restart all"
echo ""

