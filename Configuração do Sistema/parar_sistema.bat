@echo off
chcp 65001 >nul
title Parar Sistema - Chatbot Cobrança
color 0C

echo ========================================
echo   PARANDO SISTEMA
echo ========================================
echo.
echo Este script irá encerrar:
echo   - Servidor Django (porta 8000)
echo   - Bot WhatsApp (porta 3001)
echo.

REM Matar processos do Django
echo 🔍 Procurando processos do Django...
for /f "tokens=2" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo ⚠️  Encerrando processo Django (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

REM Matar processos do Node/Bot
echo 🔍 Procurando processos do Bot...
for /f "tokens=2" %%a in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (
    echo ⚠️  Encerrando processo Bot (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

REM Matar processos do Node.js relacionados
taskkill /F /IM node.exe >nul 2>&1

echo.
echo ✅ Sistema parado!
echo.
pause

