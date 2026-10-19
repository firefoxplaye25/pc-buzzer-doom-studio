@echo off
title Teste do Buzzer da Placa-Mae com Privilegios
echo ========================================================
echo   TESTANDO BUZZER DA PLACA-MAE (WinRing0 / Porta 0x61)
echo ========================================================
echo.
echo Executando pc-beeper como Administrador para acessar a porta 0x61...
echo (Se aparecer a janela do Windows pedindo permissao, clique em SIM!)
echo.
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0pc_beeper\" && pc-beeper.exe -f 1000 -d 800' -Verb RunAs"
echo Comando enviado!
pause
