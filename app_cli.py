"""
PC Buzzer Music Studio - Modo Terminal (CLI)
Executa músicas retrô e bips pelo buzzer ou emulador via linha de comando.
"""

import sys
import time
import os
from buzzer_engine import BuzzerEngine, note_to_freq, NOTE_FREQS
from songs import SONG_CATALOG, parse_rtttl, get_song_notes

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("\033[96m" + r"""
   ___   ____   ___  __  __________  __________
  / _ \ / ___/  / _ )/ / / /_  /_  / / __/ _ \ \
 / ___// /__   / _  / /_/ / / /_/ /_/ _// , _/ /
/_/    \___/  /____/\____/ /___/___/___/_/|_|/_/ 
   >> PC BUZZER 8-BIT MUSIC PLAYER (WINDOWS) <<
    """ + "\033[0m")

def print_oscillo_ascii(freq):
    if freq <= 0:
        return "       [ PAUSA / REST ]"
    # Barra ASCII de frequência
    bars = min(40, max(2, int(freq / 50)))
    return f" \033[93m{freq:4d} Hz\033[0m [\033[92m{'█' * bars}\033[0m{' ' * (40 - bars)}]"

def play_song_cli(engine, song_name, notes):
    clear_screen()
    print_banner()
    print(f"\033[95m▶ Reproduzindo: {song_name}\033[0m")
    print(f"Total de notas: {len(notes)}")
    print("Pressione Ctrl+C para interromper a música a qualquer momento.\n")

    try:
        for idx, (note_or_freq, duration) in enumerate(notes):
            freq = note_or_freq if isinstance(note_or_freq, int) else note_to_freq(note_or_freq)
            vis = print_oscillo_ascii(freq)
            sys.stdout.write(f"\rNota {idx+1:3d}/{len(notes)}: {vis} ")
            sys.stdout.flush()
            engine.play_note(freq, duration)
            time.sleep(0.02)
        print("\n\n\033[92m✔ Música concluída!\033[0m")
    except KeyboardInterrupt:
        print("\n\n\033[91m⏹ Reprodução interrompida pelo usuário.\033[0m")
    input("\nPressione [Enter] para voltar ao menu...")

def interactive_keyboard(engine):
    clear_screen()
    print_banner()
    print("\033[93m=== TECLADO PIANO BUZZER (Digite as notas) ===\033[0m")
    print("Digite a nota (ex: C4, D4, E4, F4, G4, A4, B4, C5) ou a frequência em Hz (ex: 440, 1000).")
    print("Para tocar várias notas em sequência, separe por espaço (ex: 'C4 E4 G4 C5')")
    print("Digite 'sair' para voltar ao menu.\n")

    while True:
        try:
            cmd = input("\033[96mNota ou Hz > \033[0m").strip().upper()
            if not cmd or cmd in ('SAIR', 'EXIT', 'Q'):
                break

            tokens = cmd.split()
            for token in tokens:
                if token.isdigit():
                    freq = int(token)
                else:
                    freq = note_to_freq(token)

                if freq > 0:
                    print(f"  -> Tocando {token} ({freq} Hz)...")
                    engine.play_note(freq, 250)
                    time.sleep(0.05)
                else:
                    print(f"  [!] Nota desconhecida: {token}")
        except KeyboardInterrupt:
            break

def main():
    # Habilita cores ANSI no terminal Windows
    os.system('')
    engine = BuzzerEngine()
    engine.mode = 'hybrid'  # Garante áudio

    while True:
        clear_screen()
        print_banner()
        print(f"Modo atual do Buzzer: \033[92m{engine.mode.upper()}\033[0m")
        print("\nEscolha uma opção:")
        print("  \033[93m[1]\033[0m Ver e Tocar Músicas Prontas (Mario, Star Wars, Tetris, etc.)")
        print("  \033[93m[2]\033[0m Teclado / Piano Interativo")
        print("  \033[93m[3]\033[0m Tocar código RTTTL personalizado")
        print("  \033[93m[4]\033[0m Alterar Modo do Buzzer (Hardware / Híbrido / Sintetizador)")
        print("  \033[93m[5]\033[0m Executar Diagnóstico Completo de Hardware")
        print("  \033[93m[6]\033[0m Abrir Interface Gráfica Completa (GUI)")
        print("  \033[91m[0]\033[0m Sair")

        choice = input("\nOpção > ").strip()

        if choice == '1':
            clear_screen()
            print_banner()
            print("\033[93m=== CATÁLOGO DE MÚSICAS ===\033[0m\n")
            song_keys = list(SONG_CATALOG.keys())
            for idx, s in enumerate(song_keys):
                print(f"  [{idx+1:2d}] {s}")
            print("\n  [0] Voltar")

            sel = input("\nEscolha o número da música > ").strip()
            if sel.isdigit():
                num = int(sel)
                if 1 <= num <= len(song_keys):
                    sname = song_keys[num - 1]
                    notes = get_song_notes(sname)
                    play_song_cli(engine, sname, notes)

        elif choice == '2':
            interactive_keyboard(engine)

        elif choice == '3':
            clear_screen()
            print_banner()
            print("\033[93m=== REPRODUTOR RTTTL PERSONALIZADO ===\033[0m")
            print("Exemplo: MinhaMelodia:d=4,o=5,b=120:c,d,e,f,g,a,b,c6\n")
            code = input("Cole a string RTTTL: ").strip()
            if code:
                try:
                    notes = parse_rtttl(code)
                    title = code.split(':')[0] if ':' in code else "Personalizada"
                    play_song_cli(engine, title, notes)
                except Exception as e:
                    print(f"\033[91mErro ao ler RTTTL: {e}\033[0m")
                    input("\nPressione Enter para continuar...")

        elif choice == '4':
            clear_screen()
            print_banner()
            print("Selecione o modo de acionamento do som:")
            print("  [1] Híbrido (Envia para Hardware Beep + Sintetizador 1-Bit)")
            print("  [2] Apenas Hardware Beep (Driver \\Device\\Beep do Windows)")
            print("  [3] Apenas Sintetizador Piezo Retrô (Onda Quadrada 1-bit)")
            m_sel = input("\nOpção > ").strip()
            if m_sel == '1':
                engine.mode = 'hybrid'
            elif m_sel == '2':
                engine.mode = 'hardware'
            elif m_sel == '3':
                engine.mode = 'synth'

        elif choice == '5':
            import test_buzzer
            test_buzzer.test_hardware_beep()
            test_buzzer.test_device_beep_ioctl()
            test_buzzer.test_square_wave_synth()
            input("\nPressione Enter para voltar ao menu...")

        elif choice == '6':
            import subprocess
            subprocess.Popen([sys.executable, "app_gui.py"])
            print("Interface gráfica iniciada!")
            time.sleep(1)

        elif choice == '0':
            engine.close()
            print("\nAté logo!")
            break

if __name__ == '__main__':
    main()
