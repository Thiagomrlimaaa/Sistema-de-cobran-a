@echo off
chcp 65001 >nul
title Iniciar Sistema Completo - Chatbot Cobrança
color 0E

echo ========================================
echo   INICIANDO SISTEMA COMPLETO
echo ========================================
echo.
echo Este script irá abrir 2 janelas:
echo   1. Django (Interface Web)
echo   2. Bot WhatsApp
echo.
echo ⚠️  NÃO FECHE AS JANELAS que serão abertas!
echo.
pause

cd /d "%~dp0\.."

REM Verificar se os arquivos necessários existem
if not exist "manage.py" (
    echo ❌ ERRO: Arquivo manage.py não encontrado!
    echo Certifique-se de estar na pasta correta do projeto.
    pause
    exit /b 1
)

if not exist "cobranca-bot\package.json" (
    echo ❌ ERRO: Pasta cobranca-bot não encontrada!
    pause
    exit /b 1
)

echo.
echo 🚀 Abrindo janelas...
echo.

REM Iniciar Django em nova janela
start "Django - Chatbot Cobrança" cmd /k "%~dp0iniciar_django.bat"

REM Aguardar um pouco antes de iniciar o bot
timeout /t 3 /nobreak >nul

REM Iniciar Bot em nova janela
start "Bot WhatsApp - Chatbot Cobrança" cmd /k "%~dp0iniciar_bot.bat"

echo.
echo ✅ Sistema iniciado!
echo.
echo 📱 Acesse: http://localhost:8000
echo.
echo As 2 janelas foram abertas. Mantenha-as abertas!
echo.
echo Para parar o sistema, feche as 2 janelas abertas.
echo.
pause

