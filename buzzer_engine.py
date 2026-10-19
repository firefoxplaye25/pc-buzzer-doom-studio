"""
Módulo de controle do Buzzer para Windows.
Oferece suporte a:
1. Windows API Beep direto (kernel32.Beep e \\Device\\Beep)
2. Sintetizador de Buzzer Piezoelétrico (Onda Quadrada Pura 1-bit retro)
"""

import sys
import time
import math
import wave
import struct
import io
import threading
import ctypes
from ctypes import wintypes

# Frequências das notas musicais (Hz)
NOTE_FREQS = {
    # Oitava 3
    'C3': 131, 'CS3': 139, 'D3': 147, 'DS3': 156, 'E3': 165, 'F3': 175,
    'FS3': 185, 'G3': 196, 'GS3': 208, 'A3': 220, 'AS3': 233, 'B3': 247,
    # Oitava 4 (Padrão)
    'C4': 262, 'CS4': 277, 'D4': 294, 'DS4': 311, 'E4': 330, 'F4': 349,
    'FS4': 370, 'G4': 392, 'GS4': 415, 'A4': 440, 'AS4': 466, 'B4': 494,
    # Oitava 5
    'C5': 523, 'CS5': 554, 'D5': 587, 'DS5': 622, 'E5': 659, 'F5': 698,
    'FS5': 740, 'G5': 784, 'GS5': 831, 'A5': 880, 'AS5': 932, 'B5': 988,
    # Oitava 6
    'C6': 1047, 'CS6': 1109, 'D6': 1175, 'DS6': 1245, 'E6': 1319, 'F6': 1397,
    'FS6': 1480, 'G6': 1568, 'GS6': 1661, 'A6': 1760, 'AS6': 1865, 'B6': 1976,
    # Oitava 7
    'C7': 2093, 'CS7': 2217, 'D7': 2349, 'DS7': 2489, 'E7': 2637, 'F7': 2794,
    'FS7': 2960, 'G7': 3136, 'GS7': 3322, 'A7': 3520, 'AS7': 3729, 'B7': 3951,
    # Pausa
    'REST': 0, 'P': 0, '_': 0
}

# Suporte a sustenidos em notação '#' e 'b'
def note_to_freq(note_name: str) -> int:
    if not note_name:
        return 0
    note_name = note_name.strip().upper()
    if note_name in ('REST', 'PAUSE', 'P', '_', '0'):
        return 0
    note_name = note_name.replace('#', 'S')
    # Conversão de bemol para sustenido correspondente
    bemol_map = {
        'DB': 'CS', 'EB': 'DS', 'GB': 'FS', 'AB': 'GS', 'BB': 'AS'
    }
    for b, s in bemol_map.items():
        if note_name.startswith(b):
            note_name = note_name.replace(b, s, 1)
            break
    return NOTE_FREQS.get(note_name, 0)


from hardware_buzzer import MotherboardBuzzer

class BEEP_SET_PARAMETERS(ctypes.Structure):
    _fields_ = [
        ('Frequency', ctypes.c_ulong),
        ('Duration', ctypes.c_ulong)
    ]


class BuzzerEngine:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.winmm = ctypes.windll.winmm
        self.is_playing = False
        self.is_paused = False
        self.stop_requested = False
        self.mode = 'hardware'  # Dispara diretamente o Beep nativo do sistema / placa-mãe
        self.current_song_name = ""
        self.current_note = ""
        self.current_freq = 0
        self.speed_multiplier = 1.0
        self.octave_shift = 0
        self._thread = None
        self._callback = None

        # Tenta carregar o driver direto da placa-mãe (Porta 0x61)
        self.mb_buzzer = MotherboardBuzzer()
        self.is_hardware_available = self.mb_buzzer.is_ready

    def set_callback(self, cb):
        """Callback(event_type, data) para atualizar UI em tempo real"""
        self._callback = cb

    def _notify(self, event_type, data=None):
        if self._callback:
            try:
                self._callback(event_type, data)
            except Exception:
                pass

    def play_raw_hardware_beep(self, freq: int, duration_ms: int):
        """Toca diretamente na porta 0x61 da placa-mãe se disponível, ou via Windows Beep"""
        if freq < 37 or freq > 32767:
            time.sleep(duration_ms / 1000.0)
            return

        # 1. Aciona o driver de hardware / pc-beeper da placa-mãe (Porta 0x61)
        if self.mb_buzzer:
            self.mb_buzzer.beep(freq, duration_ms)
            return

        # 2. Caso contrário, envia para a API do Windows
        try:
            import winsound
            winsound.Beep(int(freq), int(duration_ms))
        except Exception:
            try:
                self.kernel32.Beep(ctypes.c_ulong(freq), ctypes.c_ulong(duration_ms))
            except Exception:
                time.sleep(duration_ms / 1000.0)

    def play_synth_square_wave(self, freq: int, duration_ms: int):
        """
        Gera uma onda quadrada de 1-bit pura na memória (WAV).
        Isso soa IDÊNTICO a um buzzer piezoelétrico físico, mesmo que o Windows
        não consiga acessar o hardware interno ou se o PC não tiver o buzzer soldado.
        """
        if freq < 37 or freq > 20000:
            time.sleep(duration_ms / 1000.0)
            return

        sample_rate = 22050
        duration_sec = duration_ms / 1000.0
        num_samples = int(sample_rate * duration_sec)
        if num_samples <= 0:
            return

        period = sample_rate / float(freq)
        amplitude = 14000  # volume bom e claro

        # Gera onda quadrada (buzzer piezoelétrico)
        buffer = bytearray()
        for i in range(num_samples):
            val = amplitude if (i % period) < (period / 2.0) else -amplitude
            buffer.extend(struct.pack('<h', val))

        # Cria container WAV em memória
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buffer)

        wav_bytes = wav_io.getvalue()

        SND_MEMORY = 0x0004
        SND_SYNC = 0x0000
        SND_NODEFAULT = 0x0002
        try:
            self.winmm.PlaySoundW(wav_bytes, None, SND_MEMORY | SND_SYNC | SND_NODEFAULT)
        except Exception:
            time.sleep(duration_sec)

    def play_note(self, note_or_freq, duration_ms: int):
        """Toca uma única nota ou frequência no modo ativo"""
        if isinstance(note_or_freq, str):
            freq = note_to_freq(note_or_freq)
            note_str = note_or_freq
        else:
            freq = int(note_or_freq)
            note_str = f"{freq}Hz"

        # Aplica deslocamento de oitava se for nota com frequência válida
        if freq > 0 and self.octave_shift != 0:
            factor = 2 ** self.octave_shift
            freq = int(freq * factor)

        duration_ms = int(duration_ms / self.speed_multiplier)
        if duration_ms < 10:
            duration_ms = 10

        self.current_note = note_str
        self.current_freq = freq
        self._notify('note_on', {'note': note_str, 'freq': freq, 'duration': duration_ms})

        if freq <= 0:
            time.sleep(duration_ms / 1000.0)
        else:
            if self.mode == 'hardware':
                self.play_raw_hardware_beep(freq, duration_ms)
            elif self.mode == 'synth':
                self.play_synth_square_wave(freq, duration_ms)
            else:  # hybrid
                # Tenta hardware Beep (winsound); se falhar ou não produzir som, usa onda sintetizada
                try:
                    self.play_raw_hardware_beep(freq, duration_ms)
                except Exception:
                    self.play_synth_square_wave(freq, duration_ms)

        self._notify('note_off', {'note': note_str, 'freq': freq})
        self.current_note = ""
        self.current_freq = 0

    def play_melody(self, song_name: str, notes_list: list):
        """
        Toca uma lista de notas [(nota_ou_freq, duracao_ms), ...]
        Executado em background thread.
        """
        self.stop(notify=False)
        self.stop_requested = False
        self.is_playing = True
        self.is_paused = False
        self.current_song_name = song_name

        def _worker():
            self._notify('start', {'song': song_name, 'total_notes': len(notes_list)})
            total = len(notes_list)
            for idx, item in enumerate(notes_list):
                if self.stop_requested:
                    break

                while self.is_paused and not self.stop_requested:
                    time.sleep(0.05)

                if self.stop_requested:
                    break

                note, dur = item
                self._notify('progress', {'current': idx + 1, 'total': total, 'note': str(note), 'duration': dur})
                self.play_note(note, dur)
                # Pequena folga entre notas para dar o efeito de articulação do buzzer
                time.sleep(0.015)

            self.is_playing = False
            self.current_song_name = ""
            self._notify('stop')

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def pause(self):
        self.is_paused = not self.is_paused
        self._notify('pause_toggle', self.is_paused)

    def stop(self, notify=True):
        self.stop_requested = True
        self.is_paused = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        self.is_playing = False
        self.current_song_name = ""
        if notify:
            self._notify('stop')

    def close(self):
        self.stop(notify=False)
        if self.mb_buzzer:
            try:
                self.mb_buzzer.close()
            except Exception:
                pass
