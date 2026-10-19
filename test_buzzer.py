"""
Script direto para testar o Beep do PC no terminal.
"""

import sys
import time
import winsound
import ctypes

def main():
    print("==================================================")
    print("      TESTE DIRETO DE BEEP DA PLACA-MÃE           ")
    print("==================================================")
    print("Disparando pulsos diretos de frequência:")
    
    escalas = [
        ("Dó (C4)", 262),
        ("Ré (D4)", 294),
        ("Mi (E4)", 330),
        ("Fá (F4)", 349),
        ("Sol (G4)", 392),
        ("Lá (A4)", 440),
        ("Si (B4)", 494),
        ("Dó (C5)", 523)
    ]

    for nome, freq in escalas:
        print(f"  -> {nome} - {freq} Hz...")
        winsound.Beep(freq, 250)
        time.sleep(0.05)

    print("\n[OK] Teste concluído!")

if __name__ == '__main__':
    main()
