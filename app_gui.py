"""
PC Buzzer Music Studio - Interface Gráfica Retrô Chiptune
Compatível com Windows 10/11: Suporta Beep da Placa-mãe e Sintetizador Retrô 1-bit.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from buzzer_engine import BuzzerEngine, note_to_freq, NOTE_FREQS
from songs import SONG_CATALOG, parse_rtttl, get_song_notes

# Cores tema Retrô Cyberpunk / Synthwave
BG_DARK = "#12131C"
BG_PANEL = "#1C1E2D"
BG_CARD = "#25283B"
ACCENT_CYAN = "#00F0FF"
ACCENT_PINK = "#FF007F"
ACCENT_YELLOW = "#FFE600"
ACCENT_GREEN = "#39FF14"
TEXT_COLOR = "#E2E8F0"
TEXT_MUTED = "#8A92A6"
KEY_WHITE = "#E6EBF2"
KEY_BLACK = "#15161E"
KEY_ACTIVE = "#00F0FF"

class BuzzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PC Buzzer Music Studio ⚡ 8-Bit Chiptune Player")
        self.geometry("920x720")
        self.minsize(840, 640)
        self.configure(bg=BG_DARK)

        self.engine = BuzzerEngine()
        self.engine.mode = 'hybrid'  # padrão seguro e audível
        self.engine.set_callback(self._on_engine_event)

        # Mapeamento do teclado do PC para notas de piano
        self.key_map = {
            'a': 'C4', 'w': 'CS4', 's': 'D4', 'e': 'DS4', 'd': 'E4', 'f': 'F4',
            't': 'FS4', 'g': 'G4', 'y': 'GS4', 'h': 'A4', 'u': 'AS4', 'j': 'B4',
            'k': 'C5', 'o': 'CS5', 'l': 'D5', 'p': 'DS5', 'ç': 'E5', ';': 'E5',
            'z': 'C3', 'x': 'D3', 'c': 'E3', 'v': 'F3', 'b': 'G3', 'n': 'A3', 'm': 'B3'
        }

        self.piano_buttons = {}
        self._build_ui()
        self._bind_keys()

    def _build_ui(self):
        # Header / Top Bar
        header = tk.Frame(self, bg=BG_PANEL, height=80, relief=tk.FLAT)
        header.pack(fill=tk.X, side=tk.TOP, padx=15, pady=(15, 10))

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side=tk.LEFT, padx=15, pady=10)

        title_lbl = tk.Label(
            title_box,
            text="⚡ PC BUZZER MUSIC STUDIO",
            font=("Impact", 22),
            fg=ACCENT_CYAN,
            bg=BG_PANEL
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            title_box,
            text="Tocador de Músicas no Buzzer / Alto-Falante da Placa-Mãe (Windows)",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_PANEL
        )
        sub_lbl.pack(anchor="w")

        # Seleção de Modo do Buzzer (Hardware / Híbrido / Sintetizador)
        mode_box = tk.Frame(header, bg=BG_PANEL)
        mode_box.pack(side=tk.RIGHT, padx=15, pady=10)

        mode_lbl = tk.Label(
            mode_box,
            text="MODO DO BUZZER:",
            font=("Segoe UI Bold", 9),
            fg=ACCENT_YELLOW,
            bg=BG_PANEL
        )
        mode_lbl.pack(anchor="e")

        self.mode_var = tk.StringVar(value="hardware (Buzzer Direto / Beep da Placa-Mãe)")
        mode_menu = ttk.Combobox(
            mode_box,
            textvariable=self.mode_var,
            state="readonly",
            values=[
                "hardware (Buzzer Direto / Beep da Placa-Mãe)",
                "synth (Sintetizador 1-Bit Retrô)",
                "hybrid (Beep + Sintetizador)"
            ],
            width=42
        )
        mode_menu.pack(anchor="e", pady=3)
        mode_menu.bind("<<ComboboxSelected>>", self._on_mode_change)

        test_beep_btn = tk.Button(
            mode_box,
            text="🔔 TESTAR BIP AGORA",
            font=("Segoe UI Bold", 8),
            bg=ACCENT_CYAN,
            fg="#000000",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._quick_test_beep
        )
        test_beep_btn.pack(anchor="e", pady=(2, 0))

        # Tabs Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_PANEL, foreground=TEXT_COLOR, padding=[16, 8], font=("Segoe UI Bold", 10))
        style.map("TNotebook.Tab", background=[("selected", BG_CARD)], foreground=[("selected", ACCENT_CYAN)])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # Aba 1: Jukebox / Músicas Clássicas
        self.tab_jukebox = tk.Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(self.tab_jukebox, text="📻 Músicas Prontas (Jukebox)")
        self._build_jukebox_tab()

        # Aba 2: Teclado de Piano Virtual ao Vivo
        self.tab_piano = tk.Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(self.tab_piano, text="🎹 Piano Buzzer ao Vivo")
        self._build_piano_tab()

        # Aba 3: Compositor RTTTL / Código Personalizado
        self.tab_composer = tk.Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(self.tab_composer, text="📝 Compositor / RTTTL")
        self._build_composer_tab()

        # Barra de Status e Visualizador Inferior
        self._build_status_bar()

    def _build_jukebox_tab(self):
        container = tk.Frame(self.tab_jukebox, bg=BG_DARK)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Painel Esquerdo: Lista de Músicas
        left_panel = tk.Frame(container, bg=BG_CARD, width=340, padx=12, pady=12)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_panel.pack_propagate(False)

        lbl = tk.Label(left_panel, text="CATÁLOGO CHIPTUNE", font=("Impact", 13), fg=ACCENT_YELLOW, bg=BG_CARD)
        lbl.pack(anchor="w", pady=(0, 8))

        # Listbox com Scrollbar
        list_frame = tk.Frame(left_panel, bg=BG_CARD)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.song_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg=BG_DARK,
            fg=TEXT_COLOR,
            selectbackground=ACCENT_CYAN,
            selectforeground="#000000",
            font=("Consolas", 10, "bold"),
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=ACCENT_CYAN,
            activestyle='none'
        )
        self.song_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.song_listbox.yview)

        for song_name in SONG_CATALOG.keys():
            self.song_listbox.insert(tk.END, song_name)

        if self.song_listbox.size() > 0:
            self.song_listbox.selection_set(0)

        # Painel Direito: Controles e Visualizador
        right_panel = tk.Frame(container, bg=BG_PANEL, padx=20, pady=20)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Monitor de Reprodução
        self.now_playing_lbl = tk.Label(
            right_panel,
            text="Pronto para tocar",
            font=("Impact", 18),
            fg=ACCENT_GREEN,
            bg=BG_PANEL
        )
        self.now_playing_lbl.pack(anchor="w", pady=(0, 5))

        self.note_display_lbl = tk.Label(
            right_panel,
            text="Nota: -- | Freq: -- Hz",
            font=("Consolas", 14, "bold"),
            fg=ACCENT_CYAN,
            bg=BG_PANEL
        )
        self.note_display_lbl.pack(anchor="w", pady=(0, 15))

        # Canvas Osciloscópio / Frequencímetro Retrô
        self.canvas_osc = tk.Canvas(right_panel, bg="#0A0B10", height=140, highlightthickness=1, highlightbackground=ACCENT_CYAN)
        self.canvas_osc.pack(fill=tk.X, pady=(0, 15))
        self._draw_oscilloscope_idle()

        # Barra de Progresso
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(right_panel, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))

        # Controles de Velocidade (BPM) e Oitava
        sliders_frame = tk.Frame(right_panel, bg=BG_PANEL)
        sliders_frame.pack(fill=tk.X, pady=(0, 15))

        # Velocidade
        speed_box = tk.Frame(sliders_frame, bg=BG_PANEL)
        speed_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.speed_lbl = tk.Label(speed_box, text="Velocidade: 1.0x", font=("Segoe UI Bold", 9), fg=TEXT_COLOR, bg=BG_PANEL)
        self.speed_lbl.pack(anchor="w")

        self.speed_scale = tk.Scale(
            speed_box,
            from_=0.5,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            bg=BG_PANEL,
            fg=TEXT_COLOR,
            troughcolor=BG_DARK,
            activebackground=ACCENT_CYAN,
            highlightthickness=0,
            command=self._on_speed_change
        )
        self.speed_scale.set(1.0)
        self.speed_scale.pack(fill=tk.X)

        # Oitava
        oct_box = tk.Frame(sliders_frame, bg=BG_PANEL)
        oct_box.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        self.oct_lbl = tk.Label(oct_box, text="Deslocamento Oitava: 0", font=("Segoe UI Bold", 9), fg=TEXT_COLOR, bg=BG_PANEL)
        self.oct_lbl.pack(anchor="w")

        self.oct_scale = tk.Scale(
            oct_box,
            from_=-2,
            to=2,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg=BG_PANEL,
            fg=TEXT_COLOR,
            troughcolor=BG_DARK,
            activebackground=ACCENT_PINK,
            highlightthickness=0,
            command=self._on_octave_change
        )
        self.oct_scale.set(0)
        self.oct_scale.pack(fill=tk.X)

        # Botões de Ação Play / Pause / Stop
        btn_frame = tk.Frame(right_panel, bg=BG_PANEL)
        btn_frame.pack(fill=tk.X, pady=10)

        play_btn = tk.Button(
            btn_frame,
            text="▶ TOCAR NO BUZZER",
            font=("Segoe UI Black", 11),
            bg=ACCENT_CYAN,
            fg="#000000",
            activebackground="#80FFFF",
            padx=16,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._play_selected_song
        )
        play_btn.pack(side=tk.LEFT, padx=(0, 10))

        pause_btn = tk.Button(
            btn_frame,
            text="⏸ PAUSAR",
            font=("Segoe UI Bold", 10),
            bg=BG_CARD,
            fg=TEXT_COLOR,
            activebackground=BG_DARK,
            padx=14,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._pause_song
        )
        pause_btn.pack(side=tk.LEFT, padx=(0, 10))

        stop_btn = tk.Button(
            btn_frame,
            text="⏹ PARAR",
            font=("Segoe UI Bold", 10),
            bg="#8A1C2A",
            fg="#FFFFFF",
            activebackground="#B5283B",
            padx=14,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._stop_song
        )
        stop_btn.pack(side=tk.LEFT)

    def _build_piano_tab(self):
        container = tk.Frame(self.tab_piano, bg=BG_DARK, padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        info_lbl = tk.Label(
            container,
            text="Toque as teclas na tela ou use seu TECLADO DO COMPUTADOR (A, W, S, E, D, F, T, G, Y, H, U, J, K)",
            font=("Segoe UI Bold", 11),
            fg=ACCENT_YELLOW,
            bg=BG_DARK
        )
        info_lbl.pack(pady=(0, 20))

        # Piano Frame
        piano_frame = tk.Frame(container, bg="#0D0E15", height=240, padx=10, pady=10, relief=tk.SOLID, borderwidth=1)
        piano_frame.pack(fill=tk.X, pady=(0, 20))

        # Teclas C4 a B5
        white_notes = [
            ('C4', 'A'), ('D4', 'S'), ('E4', 'D'), ('F4', 'F'),
            ('G4', 'G'), ('A4', 'H'), ('B4', 'J'), ('C5', 'K'),
            ('D5', 'L'), ('E5', 'Ç'), ('F5', 'Z'), ('G5', 'X'),
            ('A5', 'C'), ('B5', 'V')
        ]

        black_notes = [
            ('CS4', 'W', 0), ('DS4', 'E', 1),
            ('FS4', 'T', 3), ('GS4', 'Y', 4), ('AS4', 'U', 5),
            ('CS5', 'O', 7), ('DS5', 'P', 8),
            ('FS5', 'B', 10), ('GS5', 'N', 11), ('AS5', 'M', 12)
        ]

        # White keys container
        white_keys_box = tk.Frame(piano_frame, bg="#0D0E15")
        white_keys_box.pack(fill=tk.BOTH, expand=True)

        white_width = 52
        white_height = 200

        for idx, (note, key_char) in enumerate(white_notes):
            btn = tk.Button(
                white_keys_box,
                text=f"{note}\n\n[{key_char}]",
                font=("Consolas", 9, "bold"),
                bg=KEY_WHITE,
                fg="#1A1A1A",
                activebackground=KEY_ACTIVE,
                relief=tk.RAISED,
                borderwidth=2,
                cursor="hand2",
                command=lambda n=note: self._play_single_note_async(n)
            )
            btn.place(x=idx * (white_width + 3), y=0, width=white_width, height=white_height)
            self.piano_buttons[note] = btn

        # Black keys
        black_width = 34
        black_height = 120
        for note, key_char, white_idx in black_notes:
            pos_x = white_idx * (white_width + 3) + (white_width - (black_width // 2))
            btn = tk.Button(
                white_keys_box,
                text=f"{note}\n[{key_char}]",
                font=("Consolas", 8, "bold"),
                bg=KEY_BLACK,
                fg=ACCENT_CYAN,
                activebackground=ACCENT_PINK,
                relief=tk.RAISED,
                borderwidth=2,
                cursor="hand2",
                command=lambda n=note: self._play_single_note_async(n)
            )
            btn.place(x=pos_x, y=0, width=black_width, height=black_height)
            self.piano_buttons[note] = btn

        # Nota tocada no momento
        self.live_note_lbl = tk.Label(
            container,
            text="Pressione uma tecla para ouvir o buzzer!",
            font=("Impact", 16),
            fg=ACCENT_CYAN,
            bg=BG_DARK
        )
        self.live_note_lbl.pack(pady=10)

    def _build_composer_tab(self):
        container = tk.Frame(self.tab_composer, bg=BG_DARK, padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        desc = tk.Label(
            container,
            text="Cole ou escreva uma melodia em formato RTTTL (Ring Tone Text Transfer Language):",
            font=("Segoe UI Bold", 10),
            fg=TEXT_COLOR,
            bg=BG_DARK
        )
        desc.pack(anchor="w", pady=(0, 8))

        self.rtttl_text = tk.Text(
            container,
            height=6,
            bg=BG_CARD,
            fg=ACCENT_GREEN,
            insertbackground="#FFFFFF",
            font=("Consolas", 11),
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.rtttl_text.pack(fill=tk.X, pady=(0, 15))
        # Exemplo padrão
        default_song = "MinhaMelodia:d=4,o=5,b=120:c,d,e,f,g,a,b,c6"
        self.rtttl_text.insert(tk.END, default_song)

        btn_row = tk.Frame(container, bg=BG_DARK)
        btn_row.pack(fill=tk.X, pady=(0, 15))

        test_play_btn = tk.Button(
            btn_row,
            text="▶ TOCAR ESTA MÚSICA",
            font=("Segoe UI Bold", 10),
            bg=ACCENT_PINK,
            fg="#FFFFFF",
            activebackground="#FF4DA6",
            padx=16,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._play_custom_rtttl
        )
        test_play_btn.pack(side=tk.LEFT, padx=(0, 10))

        stop_custom_btn = tk.Button(
            btn_row,
            text="⏹ PARAR",
            font=("Segoe UI Bold", 10),
            bg=BG_PANEL,
            fg=TEXT_COLOR,
            padx=14,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._stop_song
        )
        stop_custom_btn.pack(side=tk.LEFT)

        # Cheatsheet explicativo
        help_box = tk.LabelFrame(container, text=" Guia Rápido de RTTTL ", font=("Segoe UI Bold", 9), fg=ACCENT_YELLOW, bg=BG_CARD, padx=12, pady=10)
        help_box.pack(fill=tk.BOTH, expand=True)

        help_text = (
            "Estrutura: Nome:d=duração_padrão,o=oitava_padrão,b=bpm:notas\n\n"
            "Exemplo: Mario:d=4,o=5,b=100:16e6,16e6,8e6,16c6,8e6,8g6\n\n"
            "• Notas: c, d, e, f, g, a, b (e sustenido: c#, d#, f#, g#, a#)\n"
            "• Pausa: p (ex: 8p = pausa de colcheia)\n"
            "• Duração: 1=semibreve, 2=mínima, 4=semínima, 8=colcheia, 16=semicolcheia\n"
            "• Ponto de aumento: adicione ponto após a nota (ex: 16g.)"
        )
        help_lbl = tk.Label(help_box, text=help_text, justify=tk.LEFT, font=("Consolas", 9), fg=TEXT_COLOR, bg=BG_CARD)
        help_lbl.pack(anchor="w")

    def _build_status_bar(self):
        status_frame = tk.Frame(self, bg=BG_PANEL, height=35, relief=tk.FLAT)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=(0, 10))

        if self.engine.is_hardware_available:
            status_text = "● DRIVER DA PLACA-MÃE ATIVO: Conectado ao Buzzer Físico (Porta 0x61)!"
            status_color = ACCENT_GREEN
            hint_text = "Som direto no buzzer físico do gabinete!"
        else:
            status_text = "⚠️ Para o BUZZER FÍSICO da placa-mãe tocar: Execute como Administrador!"
            status_color = ACCENT_YELLOW
            hint_text = "Use o atalho: iniciar_como_administrador.bat"

        self.status_lbl = tk.Label(
            status_frame,
            text=status_text,
            font=("Segoe UI Bold", 9),
            fg=status_color,
            bg=BG_PANEL
        )
        self.status_lbl.pack(side=tk.LEFT, padx=10, pady=5)

        hardware_hint = tk.Label(
            status_frame,
            text=hint_text,
            font=("Segoe UI Bold", 8),
            fg=ACCENT_CYAN,
            bg=BG_PANEL
        )
        hardware_hint.pack(side=tk.RIGHT, padx=10, pady=5)

    def _bind_keys(self):
        # Associa teclas do teclado às notas
        self.bind("<KeyPress>", self._on_key_press)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_key_press(self, event):
        # Não intercepta se o usuário estiver digitando no Text box do compositor
        if self.focus_get() == self.rtttl_text:
            return
        key = event.char.lower()
        if key in self.key_map:
            note = self.key_map[key]
            self._play_single_note_async(note)

    def _play_single_note_async(self, note_name: str):
        self.live_note_lbl.config(text=f"Nota: {note_name} ({note_to_freq(note_name)} Hz)")
        # Anima a tecla no piano
        if note_name in self.piano_buttons:
            btn = self.piano_buttons[note_name]
            orig_bg = btn.cget("bg")
            btn.config(bg=ACCENT_CYAN)
            self.after(180, lambda b=btn, bg=orig_bg: b.config(bg=bg))

        threading.Thread(target=lambda: self.engine.play_note(note_name, 160), daemon=True).start()

    def _on_mode_change(self, event=None):
        raw = self.mode_var.get()
        if "hybrid" in raw:
            self.engine.mode = 'hybrid'
            self.status_lbl.config(text="● Modo: Híbrido (Driver Beep + Sintetizador)", fg=ACCENT_GREEN)
        elif "hardware" in raw:
            self.engine.mode = 'hardware'
            self.status_lbl.config(text="● Modo: Apenas Hardware Beep (Placa-Mãe / Windows Beep)", fg=ACCENT_YELLOW)
        else:
            self.engine.mode = 'synth'
            self.status_lbl.config(text="● Modo: Sintetizador Piezo Retrô (Onda Quadrada 1-Bit)", fg=ACCENT_CYAN)

    def _quick_test_beep(self):
        threading.Thread(target=lambda: (
            self.engine.play_note(880, 150),
            time.sleep(0.05),
            self.engine.play_note(1760, 200)
        ), daemon=True).start()

    def _on_speed_change(self, val):
        mult = float(val)
        self.engine.speed_multiplier = mult
        self.speed_lbl.config(text=f"Velocidade: {mult:.1f}x")

    def _on_octave_change(self, val):
        oct_shift = int(val)
        self.engine.octave_shift = oct_shift
        self.oct_lbl.config(text=f"Deslocamento Oitava: {oct_shift:+d}")

    def _play_selected_song(self):
        sel = self.song_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma música da lista.")
            return
        song_name = self.song_listbox.get(sel[0])
        notes = get_song_notes(song_name)
        if not notes:
            messagebox.showerror("Erro", "Não foi possível carregar as notas desta música.")
            return
        self.now_playing_lbl.config(text=f"▶ Tocando: {song_name}")
        self.engine.play_melody(song_name, notes)

    def _play_custom_rtttl(self):
        code = self.rtttl_text.get("1.0", tk.END).strip()
        if not code:
            return
        try:
            notes = parse_rtttl(code)
            song_name = code.split(':')[0] if ':' in code else "Personalizada"
            self.now_playing_lbl.config(text=f"▶ Tocando: {song_name}")
            self.engine.play_melody(song_name, notes)
        except Exception as e:
            messagebox.showerror("Erro no RTTTL", f"Falha ao interpretar código RTTTL:\n{e}")

    def _pause_song(self):
        self.engine.pause()

    def _stop_song(self):
        self.engine.stop(notify=False)
        self._reset_player_ui()

    def _reset_player_ui(self):
        self.now_playing_lbl.config(text="Pronto para tocar")
        self.note_display_lbl.config(text="Nota: -- | Freq: -- Hz")
        self.progress_var.set(0)
        self._draw_oscilloscope_idle()

    def _draw_oscilloscope_idle(self):
        self.canvas_osc.delete("all")
        w = self.canvas_osc.winfo_width()
        if w <= 1:
            w = 500
        h = 140
        mid = h // 2
        # Linha central neon
        self.canvas_osc.create_line(0, mid, w, mid, fill="#1D2A44", width=2)
        self.canvas_osc.create_text(w // 2, mid - 15, text="8-BIT BUZZER OSCILLOSCOPE", font=("Impact", 12), fill="#2C3D63")

    def _draw_oscilloscope_wave(self, freq: int):
        self.canvas_osc.delete("all")
        w = self.canvas_osc.winfo_width()
        if w <= 1:
            w = 500
        h = 140
        mid = h // 2

        if freq <= 0:
            self._draw_oscilloscope_idle()
            return

        # Desenha onda quadrada realista com frequência variável
        cycles = max(3, min(30, int(freq / 60)))
        step = w / (cycles * 2)
        amplitude = 45

        points = []
        high = True
        cur_x = 0
        while cur_x < w:
            y = mid - amplitude if high else mid + amplitude
            points.append((cur_x, y))
            cur_x += step
            points.append((cur_x, y))
            high = not high

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            self.canvas_osc.create_line(x1, y1, x2, y2, fill=ACCENT_CYAN, width=3)

        self.canvas_osc.create_text(w - 70, 20, text=f"{freq} Hz", font=("Consolas", 11, "bold"), fill=ACCENT_YELLOW)

    def _on_engine_event(self, event_type, data):
        # Eventos vêm de thread de áudio, agenda execução segura no Tkinter
        if event_type == 'note_on':
            freq = data.get('freq', 0)
            note = data.get('note', '')
            self.after(0, lambda: self._update_note_ui(note, freq))
        elif event_type == 'progress':
            cur = data.get('current', 0)
            tot = data.get('total', 1)
            pct = (cur / tot) * 100.0
            self.after(0, lambda: self.progress_var.set(pct))
        elif event_type == 'stop':
            self.after(0, self._reset_player_ui)

    def _update_note_ui(self, note_str, freq):
        self.note_display_lbl.config(text=f"Nota: {note_str} | Freq: {freq} Hz")
        self._draw_oscilloscope_wave(freq)

    def _on_close(self):
        self.engine.close()
        self.destroy()

if __name__ == '__main__':
    app = BuzzerApp()
    app.mainloop()
