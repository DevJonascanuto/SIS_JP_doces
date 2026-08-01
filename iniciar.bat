@echo off
title JP Doces - Sistema de Pedidos
cd /d "%~dp0"
echo Iniciando JP Doces...
"%~dp0.venv\Scripts\python.exe" app.py
pause
