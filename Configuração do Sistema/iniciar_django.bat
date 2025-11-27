@echo off
chcp 65001 >nul
title Django - Chatbot Cobrança
color 0A

echo ========================================
echo   INICIANDO DJANGO (Interface Web)
echo ========================================
echo.

cd /d "%~dp0\.."

REM Verificar se o venv existe
if not exist "venv\Scripts\python.exe" (
    echo ❌ ERRO: Ambiente virtual não encontrado!
    echo.
    echo Execute primeiro: "Configuração do Sistema\configurar_sistema.bat"
    pause
    exit /b 1
)

REM Verificar se as dependências estão instaladas
echo 🔍 Verificando dependências...
venv\Scripts\python.exe -c "import django" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Instalando dependências...
    venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
)

REM Aplicar migrations se necessário
echo 🔍 Verificando banco de dados...
venv\Scripts\python.exe manage.py migrate --noinput >nul 2>&1

echo.
echo ✅ Django iniciando...
echo 📱 Acesse: http://localhost:8000
echo.
echo ⚠️  Mantenha esta janela aberta!
echo.

REM Iniciar Django
venv\Scripts\python.exe manage.py runserver

pause

