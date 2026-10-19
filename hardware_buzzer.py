"""
Controlador de Hardware do Buzzer da Placa-Mãe (Porta 0x61 e PIT 8254).
Utiliza WinRing0x64 e pc-beeper.exe para comunicação direta com a placa-mãe.
"""

import os
import sys
import time
import ctypes
import subprocess

PIT_FREQ = 1193180
PORT_PIT_MODE = 0x43
PORT_PIT_CHAN2 = 0x42
PORT_SPEAKER = 0x61

class MotherboardBuzzer:
    def __init__(self):
        self.dll = None
        self.is_ready = False
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.exe_path = os.path.join(self.base_dir, "pc_beeper", "pc-beeper.exe")
        self._init_driver()

    def _init_driver(self):
        # Garante que o diretório contenha a dll
        dll_path = os.path.join(self.base_dir, "WinRing0x64.dll")
        if not os.path.exists(dll_path):
            dll_path = os.path.join(self.base_dir, "pc_beeper", "WinRing0x64.dll")

        if os.path.exists(dll_path):
            try:
                self.dll = ctypes.WinDLL(dll_path)
                self.dll.InitializeOls.restype = ctypes.c_int
                self.dll.DeinitializeOls.restype = None
                self.dll.WriteIoPortByte.argtypes = [ctypes.c_ushort, ctypes.c_ubyte]
                self.dll.WriteIoPortByte.restype = None
                self.dll.ReadIoPortByte.argtypes = [ctypes.c_ushort]
                self.dll.ReadIoPortByte.restype = ctypes.c_ubyte

                if self.dll.InitializeOls() != 0:
                    self.is_ready = True
            except Exception:
                self.is_ready = False

    def beep(self, freq: int, duration_ms: int):
        """Dispara um tom físico na porta 0x61 da placa-mãe"""
        if freq < 37 or freq > 20000:
            time.sleep(duration_ms / 1000.0)
            return

        # 1. Tenta via DLL direta (ultra rápida se inicializada como Admin)
        if self.is_ready and self.dll:
            try:
                divisor = int(PIT_FREQ / freq)
                self.dll.WriteIoPortByte(PORT_PIT_MODE, 0xB6)
                self.dll.WriteIoPortByte(PORT_PIT_CHAN2, divisor & 0xFF)
                self.dll.WriteIoPortByte(PORT_PIT_CHAN2, (divisor >> 8) & 0xFF)

                ctrl = self.dll.ReadIoPortByte(PORT_SPEAKER)
                self.dll.WriteIoPortByte(PORT_SPEAKER, ctrl | 0x03)
                time.sleep(duration_ms / 1000.0)
                ctrl = self.dll.ReadIoPortByte(PORT_SPEAKER)
                self.dll.WriteIoPortByte(PORT_SPEAKER, ctrl & 0xFC)
                return
            except Exception:
                pass

        # 2. Chama diretamente o executável pc-beeper.exe (que funcionou com sucesso!)
        if os.path.exists(self.exe_path):
            try:
                subprocess.run(
                    [self.exe_path, "-f", str(freq), "-d", str(duration_ms)],
                    cwd=os.path.dirname(self.exe_path),
                    creationflags=0x08000000
                )
                return
            except Exception:
                pass

        # 3. Fallback: Se não tiver elevação de hardware, aguarda o tempo da nota
        time.sleep(duration_ms / 1000.0)

    def stop(self):
        if self.is_ready and self.dll:
            try:
                ctrl = self.dll.ReadIoPortByte(PORT_SPEAKER)
                self.dll.WriteIoPortByte(PORT_SPEAKER, ctrl & 0xFC)
            except Exception:
                pass

    def close(self):
        self.stop()
        if self.is_ready and self.dll:
            try:
                self.dll.DeinitializeOls()
            except Exception:
                pass
            self.is_ready = False
