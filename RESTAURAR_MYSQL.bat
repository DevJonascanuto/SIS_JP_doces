@echo off
echo ============================================
echo  Restaurando MySQL - Corrigindo my.ini
echo ============================================

echo [1/3] Copiando my.ini corrigido (sem BOM)...
copy /Y "C:\PROJETOS\SIS_JP_doces\my_ini_correto.ini" "C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"
if %errorlevel%==0 (
    echo [OK] my.ini restaurado!
) else (
    echo [ERRO] Falha ao copiar my.ini
    pause
    exit /b 1
)

echo [2/3] Restaurando servico para LocalSystem...
reg add "HKLM\SYSTEM\CurrentControlSet\Services\MySQL80" /v "ObjectName" /t REG_SZ /d "LocalSystem" /f

echo [3/3] Iniciando servico MySQL80...
net start MySQL80
if %errorlevel%==0 (
    echo.
    echo [OK] MySQL80 iniciado com sucesso!
    netstat -an | findstr ":3306"
) else (
    echo [ERRO] Servico ainda falha. Tentando modo direto...
    start "MySQL80" /MIN "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini" --console
    timeout /t 6 /nobreak >nul
    netstat -an | findstr ":3306"
)
echo ============================================
pause
