"""
Toca o tema do Super Mario Bros exclusivamente através do Beep nativo do Windows (winsound.Beep).
Sem nenhuma simulação de placa de som ou arquivo WAV.
"""

import sys
import time
import winsound

# Frequências (Hz) e durações (ms)
MARIO_THEME = [
    (659, 150),  # E5
    (659, 150),  # E5
    (0, 100),    # pausa
    (659, 150),  # E5
    (0, 100),    # pausa
    (523, 150),  # C5
    (659, 200),  # E5
    (784, 350),  # G5
    (0, 200),    # pausa
    (392, 350),  # G4
    (0, 200),    # pausa
    (523, 250),  # C5
    (0, 150),
    (392, 250),  # G4
    (0, 150),
    (330, 250),  # E4
    (0, 150),
    (440, 200),  # A4
    (494, 200),  # B4
    (466, 150),  # A#4
    (440, 250),  # A4
    (392, 200),  # G4
    (659, 200),  # E5
    (784, 200),  # G5
    (880, 250),  # A5
    (698, 150),  # F5
    (784, 200),  # G5
    (659, 250),  # E5
    (523, 150),  # C5
    (587, 150),  # D5
    (494, 250),  # B4
]

print("==================================================")
print("  TOCANDO SUPER MARIO PELO BEEP DIRETO DO PC      ")
print("==================================================")
print("Pressione Ctrl+C para parar a qualquer momento.\n")

try:
    for idx, (freq, dur) in enumerate(MARIO_THEME):
        if freq == 0:
            print(f"[{idx+1:02d}/{len(MARIO_THEME)}] Pausa ({dur}ms)")
            time.sleep(dur / 1000.0)
        else:
            print(f"[{idx+1:02d}/{len(MARIO_THEME)}] Beep: {freq} Hz ({dur}ms)")
            winsound.Beep(freq, dur)
        time.sleep(0.02)
    print("\nConcluído com sucesso!")
except KeyboardInterrupt:
    print("\nParado pelo usuário.")
