@echo off
echo ============================================
echo  Configurando MySQL para iniciar no login
echo ============================================

echo [1/3] Iniciando MySQL agora...
start "MySQL80" /MIN "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"

echo Aguardando MySQL iniciar (8 segundos)...
timeout /t 8 /nobreak >nul

netstat -an | findstr "0.0.0.0:3306" >nul
if %errorlevel%==0 (
    echo [OK] MySQL rodando na porta 3306!
) else (
    echo [AVISO] MySQL pode estar iniciando ainda...
)

echo.
echo [2/3] Criando tarefa de inicio automatico no login...
schtasks /Create /TN "MySQL80-AutoStart" /TR "C:\PROJETOS\SIS_JP_doces\mysql_start.bat" /SC ONLOGON /RU "%USERDOMAIN%\%USERNAME%" /RL HIGHEST /F

echo.
echo [3/3] Verificando tarefa criada...
schtasks /Query /TN "MySQL80-AutoStart" /FO LIST

echo.
echo ============================================
echo  Pronto! MySQL iniciara automaticamente
echo  em cada login. Nao feche a janela preta
echo  do MySQL que ficar aberta em background.
echo ============================================
netstat -an | findstr ":3306"
pause
