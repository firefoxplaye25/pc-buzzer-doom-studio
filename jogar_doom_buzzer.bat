@echo off
title DOOM (1993) - PC SPEAKER BUZZER
:: Solicita permissao de Administrador para que o jogo acione o speaker da placa-mae
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Solicitando privilegios de Administrador para jogar Doom no Buzzer...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && jogar_doom_buzzer.bat' -Verb RunAs"
    exit /b
)

:: Garante caminho para todas as bibliotecas do MSYS2 UCRT64
set PATH=C:\msys64\ucrt64\bin;%PATH%

cd /d "%~dp0doom_buzzer"

:: Se houver instancia anterior aberta, finaliza
taskkill /F /IM chocolate-doom.exe >nul 2>&1
taskkill /F /IM doom_buzzer.exe >nul 2>&1

echo ========================================================
echo       DOOM (1993) ORIGINAL - SOM NO BUZZER / BIP
echo ========================================================
echo.
echo - Jogo Original id Software 1993 (DOOM1.WAD autentico)
echo - Trilha Sonora (E1M1 At Doom's Gate) e Efeitos Sonoros 100% no BUZZER da placa-mae!
echo - Prioridade inteligente: tiros e monstros tocam na hora e a musica volta suavemente!
echo - Mira livre com mouse (novert ativado, sem andar com mouse)
echo - Movimento: WASD, Abrir portas: ESPACO, Atirar: BOTAO ESQUERDO DO MOUSE
echo.

:: Forca driver de som para o PC Speaker do Windows com WinRing0
set PCSOUND_DRIVER=Windows

start "" doom_buzzer.exe -iwad DOOM1.WAD -config default.cfg -extraconfig doom_buzzer.cfg -novert
