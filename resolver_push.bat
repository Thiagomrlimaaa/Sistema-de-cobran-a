@echo off
chcp 65001 >nul
echo ========================================
echo   Resolver Erro de Push no GitHub
echo ========================================
echo.

echo O repositório remoto tem mudanças que você não tem localmente.
echo Vamos integrar essas mudanças primeiro.
echo.

echo IMPORTANTE: Use Git Bash para executar os comandos!
echo.
echo Abra Git Bash e execute:
echo.
echo cd "/c/Users/AVELL/Documents/chatbot - cobrança"
echo git pull origin main --allow-unrelated-histories
echo git push -u origin main
echo.
echo OU se preferir, execute manualmente no PowerShell:
echo.
pause

REM Tentar usar Git do caminho completo
set "GIT=C:\Program Files\Git\cmd\git.exe"

if exist "%GIT%" (
    echo.
    echo Tentando usar Git do caminho completo...
    echo.
    cd /d "%~dp0"
    
    echo Executando: git pull origin main --allow-unrelated-histories
    "%GIT%" pull origin main --allow-unrelated-histories
    
    if errorlevel 1 (
        echo.
        echo Erro ao fazer pull. Use Git Bash manualmente.
        echo.
    ) else (
        echo.
        echo Pull realizado com sucesso!
        echo.
        echo Executando: git push -u origin main
        "%GIT%" push -u origin main
        
        if errorlevel 1 (
            echo.
            echo Erro ao fazer push. Verifique os logs acima.
            echo.
        ) else (
            echo.
            echo ========================================
            echo   SUCESSO! Código enviado!
            echo ========================================
            echo.
        )
    )
) else (
    echo.
    echo Git não encontrado. Use Git Bash manualmente.
    echo.
)

pause

