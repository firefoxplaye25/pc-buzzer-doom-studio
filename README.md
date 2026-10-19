# 🔊 PC Buzzer Music Studio & DOOM (1993) no Speaker da Placa-Mãe

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%20%2F%2011%20x64-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/DOOM-1993%20id%20Software-B22222?style=for-the-badge&logo=doom&logoColor=white" />
  <img src="https://img.shields.io/badge/Driver-WinRing0%20(Ring%200)-2EA44F?style=for-the-badge&logo=c&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.10%2B%20Tkinter-FFD43B?style=for-the-badge&logo=python&logoColor=306998" />
  <img src="https://img.shields.io/badge/Hardware-PIT%208254%20Port%200x61-9B59B6?style=for-the-badge" />
</p>

Projeto de engenharia reversa e controle de hardware para fazer o **Buzzer / PC Speaker físico da placa-mãe** apitar no Windows 10 e Windows 11 modernos de 64 bits, executando **áudio de jogos retrô (DOOM 1993)** e um **Music Studio Chiptune completo em Python com Piano ao vivo e osciloscópio em tempo real**.

---

## 📑 Índice
1. [O Desafio: Por que o Buzzer não toca no Windows Moderno?](#-o-desafio-por-que-o-buzzer-não-toca-no-windows-moderno)
2. [A Solução: Como funciona o WinRing0 (Ring 0 / Kernel Mode)](#-a-solução-como-funciona-o-winring0-ring-0--kernel-mode)
3. [Arquitetura de Hardware: Portas 0x42, 0x43 e 0x61](#-arquitetura-de-hardware-portas-0x42-0x43-e-0x61)
4. [DOOM 1993: Modificação do Chocolate Doom](#-doom-1993-modificação-do-chocolate-doom)
5. [PC Buzzer Music Studio (Python)](#-pc-buzzer-music-studio-python)
6. [Passo a Passo de Instalação e Uso](#-passo-a-passo-de-instalação-e-uso)
7. [Estrutura do Repositório](#-estrutura-do-repositório)

---

## ⚠️ O Desafio: Por que o Buzzer não toca no Windows Moderno?

Nos computadores antigos com MS-DOS e Windows 95/98/XP, qualquer aplicativo podia emitir bips e músicas diretamente no alto-falante interno do gabinete. 

No entanto, no **Windows 10 e Windows 11 (arquitetura x64)**:
1. **Isolamento de Segurança (Ring 3 vs Ring 0)**: Programas de usuário rodam em **Ring 3**. O Windows x64 bloqueia estritamente instruções de máquina de entrada/saída direta de porta (`IN` e `OUT`) como medida de segurança.
2. **Redirecionamento do `beep.sys`**: A API `kernel32.dll -> Beep(freq, duration)` da Microsoft **não escreve mais no hardware do speaker interno**. Em vez disso, o Windows converte a chamada e redireciona o tom sintetizado para o seu fone de ouvido ou caixa de som padrão do Windows.
3. **Falta do Speaker Físico**: A maioria dos gabinetes modernos não traz o speaker soldado na placa-mãe. É necessário plugar um **buzzer piezoelétrico de 4 pinos** no conector frontal `SPEAKER` / `SPK` da placa-mãe.

---

## 🛡️ A Solução: Como funciona o WinRing0 (Ring 0 / Kernel Mode)

Para contornar o bloqueio do Windows sem precisar reiniciar em MS-DOS ou desativar proteções críticas do sistema, utilizamos a biblioteca **WinRing0** (`WinRing0x64.dll` e `WinRing0x64.sys`):

```
┌────────────────────────────────────────────────────────┐
│ USER SPACE (Ring 3)                                    │
│  [doom_buzzer.exe]   ou   [app_gui.py (Python)]        │
│          │                        │                    │
│          ▼                        ▼                    │
│     WinRing0x64.dll (API de Interface de Usuário)      │
└──────────────────────────┬─────────────────────────────┘
                           │ DeviceIoControl (Admin)
┌──────────────────────────▼─────────────────────────────┐
│ KERNEL SPACE (Ring 0)                                  │
│     WinRing0x64.sys (Driver de Modo Kernel)            │
│          │                                             │
│          ├──> OUT 0x43, 0xB6   (Configura PIT Timer)   │
│          ├──> OUT 0x42, Divisor (Define Frequência)    │
│          └──> OUT 0x61, Ctrl   (Liga/Desliga Speaker)  │
└──────────────────────────┬─────────────────────────────┘
                           │ Linhas Físicas do Barramento
┌──────────────────────────▼─────────────────────────────┐
│ HARDWARE DA PLACA-MÃE                                  │
│  Chip PIT 8254 ────> Conector SPK (4 pinos) ──> BUZZER │
└────────────────────────────────────────────────────────┘
```

- **Elevação como Administrador**: O script precisa ser executado como Administrador para que o Windows Service Control Manager possa carregar dinamicamente o driver `WinRing0x64.sys`.
- **`InitializeOls()`**: Inicializa o subsistema do driver em modo Kernel.
- **`WriteIoPortByte(porta, valor)`**: Emite a instrução de baixo nível `OUT` diretamente para as portas do barramento ISA/LPC da placa-mãe.
- **`ReadIoPortByte(porta)`**: Emite a instrução `IN` para ler o registrador da porta sem sobrepor outros bits do chipset.

---

## ⚙️ Arquitetura de Hardware: Portas 0x42, 0x43 e 0x61

O áudio do PC Speaker no padrão IBM PC compatível é gerado pelo chip **PIT 8254 (Programmable Interval Timer)** operando em conjunto com o **System Control Port B**:

### 1. PIT Frequência Base: `1.193.180 Hz` (1.19318 MHz)
Para gerar uma nota na frequência $F$ (em Hertz), calcula-se o divisor inteiro de 16 bits:
$$\text{Divisor} = \left\lfloor \frac{1193180}{F} \right\rfloor$$

### 2. Configuração do Modo de Onda Quadrada (Porta `0x43`)
Envia-se o byte `0xB6` (`10110110b`):
- Bits 7-6 = `10` (Canal 2 do PIT)
- Bits 5-4 = `11` (Acesso de 16 bits: primeiro byte menos significativo, depois o mais significativo)
- Bits 3-1 = `011` (Modo 3: Gerador de Onda Quadrada / Square Wave)
- Bit 0 = `0` (Contador binário de 16 bits)

### 3. Envio do Divisor de Frequência (Porta `0x42`)
```c
WriteIoPortByte(0x43, 0xB6);
WriteIoPortByte(0x42, divisor & 0xFF);        // LSB (Byte Menor)
WriteIoPortByte(0x42, (divisor >> 8) & 0xFF); // MSB (Byte Maior)
```

### 4. Ativação do Speaker Físico (Porta `0x61`)
A porta `0x61` controla a porta lógica do alto-falante:
- **Bit 0**: Habilita o portão de contagem do Canal 2 do PIT.
- **Bit 1**: Habilita os dados de áudio do Canal 2 para o pino do alto-falante.
- **Ligar o Som**: `WriteIoPortByte(0x61, ReadIoPortByte(0x61) | 0x03);`
- **Desligar o Som**: `WriteIoPortByte(0x61, ReadIoPortByte(0x61) & 0xFC);`

---

## 🎮 DOOM 1993: Modificação do Chocolate Doom

No Chocolate Doom original, os sons de PC Speaker em sistemas Windows chamam o `Beep()` da API win32. Modificamos o arquivo [`chocolate-doom/pcsound/pcsound_win32.c`](chocolate-doom/pcsound/pcsound_win32.c):

1. **Injeção Dinâmica da DLL**: Ao inicializar o som, o jogo procura `WinRing0x64.dll` e resolve os ponteiros de função `InitializeOls`, `DeinitializeOls`, `WriteIoPortByte` e `ReadIoPortByte`.
2. **Prioridade em Tempo Real**: Os efeitos sonoros (disparos de pistola/shotgun, rugidos de monstros, portas abrindo) interrompem momentaneamente as notas musicais e voltam suavemente para a trilha sonora *At Doom's Gate (E1M1)*.
3. **Modo Administrador Automático**: O script [`jogar_doom_buzzer.bat`](jogar_doom_buzzer.bat) detecta privilégios e eleva via PowerShell `Start-Process -Verb RunAs`.

---

## 🎵 PC Buzzer Music Studio (Python)

Uma suíte gráfica desenvolvida em Python/Tkinter ([`app_gui.py`](app_gui.py)) com:

- **Jukebox Chiptune 1-Bit**:
  - *Super Mario Bros (Overworld)*
  - *Star Wars (Imperial March)*
  - *Tetris (Korobeiniki)*
  - *Megalovania (Undertale)*
  - *Doom (E1M1)*
  - *The Legend of Zelda*
  - *Mortal Kombat*
  - *Plants vs. Zombies (Brainiac Maniac & Grasswalk)*
  - *Rick Astley (Never Gonna Give You Up)*
- **Osciloscópio Animado**: Visualização gráfica em tempo real da onda quadrada (square wave) e display de frequência instantânea em Hertz.
- **Piano Buzzer ao Vivo**: Toque com latência ultra-baixa (< 1ms) usando as teclas do seu teclado físico (`A`, `W`, `S`, `E`, `D`, `F`, `T`, `G`, `Y`, `H`, `U`, `J`, `K`).
- **Compositor RTTTL**: Suporte ao padrão *Ring Tone Text Transfer Language* dos antigos toques de celular Nokia.

---

## 🚀 Passo a Passo de Instalação e Uso

### 1. Conexão Física do Hardware
1. Abra seu gabinete (com o computador desligado).
2. Localize o painel de conectores frontais da sua placa-mãe (próximo aos pinos de `POWER SW`, `RESET`, `HDD LED`).
3. Conecte o **buzzer piezoelétrico de 4 pinos** nos pinos indicados como `SPEAKER` ou `SPK`.

### 2. Jogando DOOM no Buzzer
Dê duplo clique no script:
```cmd
jogar_doom_buzzer.bat
```
*O Windows solicitará confirmação de Administrador (UAC). Clique em "Sim" para ativar o driver de porta.*

### 3. Abrindo o Studio Musical
Para abrir o estúdio de chiptunes com piano ao vivo:
```cmd
iniciar_como_administrador.bat
```
Ou via terminal:
```bash
python app_gui.py
```

---

## 📂 Estrutura do Repositório

```text
├── WinRing0x64.dll              # DLL de comunicação em modo usuário
├── WinRing0x64.sys              # Driver de Kernel de 64 bits (Ring 0)
├── app_gui.py                   # Interface Gráfica completa (Tkinter + Canvas)
├── app_cli.py                   # Interface de linha de comando para terminal
├── hardware_buzzer.py           # Módulo Python com acesso direto às portas I/O
├── buzzer_engine.py             # Engine de síntese e agendamento de notas
├── songs.py                     # Catálogo de partituras e frequências
├── test_buzzer.py               # Script de teste rápido de hardware
├── jogar_doom_buzzer.bat        # Lança o Doom com prioridade no speaker
├── iniciar_como_administrador.bat# Inicia o Music Studio elevado como Admin
├── doom_buzzer/                 # Executável do Doom, WAD shareware e DLLs
├── chocolate-doom/              # Código-fonte modificado em C (pcsound_win32.c)
└── pc_beeper/                   # Utilitário de linha de comando em C para bips
```

---

## 📜 Licença e Créditos
- **DOOM**: © 1993 id Software.
- **Chocolate Doom**: Licenciado sob GNU GPL v2.
- **WinRing0**: OpenLibSys.org.
- **Desenvolvido por**: GDI Games / Firefoxplaye25.
