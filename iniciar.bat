@echo off
title PC Buzzer Music Studio
cls
echo ========================================================
echo         PC BUZZER MUSIC STUDIO (8-BIT PLAYER)
echo ========================================================
echo.
echo Escolha como deseja abrir:
echo  [1] Interface Grafica Completa (Recomendado)
echo  [2] Modo Terminal (CLI)
echo  [3] Executar Teste e Diagnostico do Buzzer
echo.
set /p opt="Digite 1, 2 ou 3: "

if "%opt%"=="2" (
    python app_cli.py
) else if "%opt%"=="3" (
    python test_buzzer.py
    pause
) else (
    start "" python app_gui.py
)
