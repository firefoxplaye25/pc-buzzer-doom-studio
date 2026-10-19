@echo off
title PC Buzzer Music Studio (Modo Administrador)
:: Verifica se ja esta executando como Administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Solicitando privilegios de Administrador para acessar a porta 0x61...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && python app_gui.py' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
python app_gui.py
