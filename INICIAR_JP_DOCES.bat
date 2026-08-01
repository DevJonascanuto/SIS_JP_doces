@echo off
title JP Doces
cd /d "%~dp0"

:: Iniciar MySQL se nao estiver rodando
netstat -an | findstr ":3306" >nul 2>&1
if %errorlevel%==0 goto iniciar_app

echo Iniciando banco de dados...
net start MySQL80
timeout /t 8 /nobreak >nul

:iniciar_app
echo Iniciando JP Doces...
start "" http://127.0.0.1:5000
"%~dp0.venv\Scripts\python.exe" app.py
