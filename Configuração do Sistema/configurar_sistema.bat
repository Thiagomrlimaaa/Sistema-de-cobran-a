@echo off
chcp 65001 >nul
title Configurar Sistema - Chatbot Cobrança
color 0C

echo ========================================
echo   CONFIGURAÇÃO INICIAL DO SISTEMA
echo ========================================
echo.
echo Este script irá:
echo   1. Verificar Python e Node.js
echo   2. Criar ambiente virtual (se necessário)
echo   3. Instalar dependências do Django
echo   4. Instalar dependências do Bot
echo   5. Configurar banco de dados
echo   6. Criar usuários de acesso
echo.
pause

cd /d "%~dp0\.."

REM Verificar Python
echo.
echo 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo Instale Python 3.11+ de: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo ✅ Python encontrado!

REM Verificar Node.js
echo.
echo 🔍 Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Node.js não encontrado!
    echo Instale Node.js 18+ de: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo ✅ Node.js encontrado!

REM Criar ambiente virtual se não existir
echo.
echo 🔍 Verificando ambiente virtual...
if not exist "venv" (
    echo ⚠️  Criando ambiente virtual...
    python -m venv venv
    echo ✅ Ambiente virtual criado!
) else (
    echo ✅ Ambiente virtual já existe!
)

REM Instalar dependências do Django
echo.
echo 📦 Instalando dependências do Django...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ ERRO ao instalar dependências do Django!
    pause
    exit /b 1
)
echo ✅ Dependências do Django instaladas!

REM Instalar dependências do Bot
echo.
echo 📦 Instalando dependências do Bot...
cd cobranca-bot
call npm install
if errorlevel 1 (
    echo ❌ ERRO ao instalar dependências do Bot!
    pause
    exit /b 1
)
cd ..
echo ✅ Dependências do Bot instaladas!

REM Aplicar migrations
echo.
echo 🔧 Configurando banco de dados...
venv\Scripts\python.exe manage.py migrate --noinput
if errorlevel 1 (
    echo ❌ ERRO ao configurar banco de dados!
    pause
    exit /b 1
)
echo ✅ Banco de dados configurado!

REM Criar usuários
echo.
echo 👤 Criando usuários de acesso...
venv\Scripts\python.exe manage.py create_users
if errorlevel 1 (
    echo ⚠️  Aviso: Não foi possível criar usuários automaticamente.
    echo Você pode criar manualmente depois.
) else (
    echo ✅ Usuários criados!
    echo    - jeff / senha: 1
    echo    - thiago / senha: 1
)

echo.
echo ========================================
echo   ✅ CONFIGURAÇÃO CONCLUÍDA!
echo ========================================
echo.
echo Agora você pode usar:
echo   - "Configuração do Sistema\iniciar_sistema.bat" (inicia tudo)
echo   - "Configuração do Sistema\iniciar_django.bat" (apenas Django)
echo   - "Configuração do Sistema\iniciar_bot.bat" (apenas Bot)
echo.
pause

