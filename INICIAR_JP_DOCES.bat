@echo off
title JP Doces

:: Iniciar MySQL se nao estiver rodando
netstat -an | findstr "0.0.0.0:3306" >nul 2>&1
if %errorlevel%==0 goto iniciar_app

echo Iniciando banco de dados...
start "" /MIN "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini" --console
timeout /t 8 /nobreak >nul

:iniciar_app
echo Iniciando JP Doces...
start "" http://127.0.0.1:5000
cd /d "C:\PROJETOS\SIS_JP_doces"
python app.py
