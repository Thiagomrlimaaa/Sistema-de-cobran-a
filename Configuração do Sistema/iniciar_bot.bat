@echo off
chcp 65001 >nul
title Bot WhatsApp - Chatbot Cobrança
color 0B

echo ========================================
echo   INICIANDO BOT WHATSAPP
echo ========================================
echo.

cd /d "%~dp0\..\cobranca-bot"

REM Verificar se node_modules existe
if not exist "node_modules" (
    echo ⚠️  Instalando dependências do Node.js...
    call npm install
    echo.
)

echo ✅ Bot iniciando...
echo 📱 API disponível em: http://localhost:3001
echo.
echo ⚠️  Mantenha esta janela aberta!
echo.

REM Iniciar bot
call npm start

pause

