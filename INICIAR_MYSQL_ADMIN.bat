@echo off
echo Corrigindo conta do servico MySQL80...
reg add "HKLM\SYSTEM\CurrentControlSet\Services\MySQL80" /v "ObjectName" /t REG_SZ /d "LocalSystem" /f
echo Iniciando MySQL80...
net start MySQL80
if %errorlevel%==0 (
    echo.
    echo [OK] MySQL iniciado com sucesso!
) else (
    echo.
    echo [ERRO] Falha. Codigo: %errorlevel%
)
pause
