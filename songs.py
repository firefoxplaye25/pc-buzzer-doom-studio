"""
Biblioteca de Músicas para Buzzer e Parser RTTTL (Ring Tone Text Transfer Language).
RTTTL é o formato clássico usado em celulares antigos e buzzers de computadores.
"""

import re
from buzzer_engine import NOTE_FREQS

# Parser RTTTL
def parse_rtttl(rtttl_string: str) -> list:
    """
    Converte uma string RTTTL padrão (ex: 'Mario:d=4,o=5,b=100:16e6,16e6,...')
    em uma lista de tuplas [(frequencia_hz, duracao_ms), ...].
    """
    parts = rtttl_string.strip().split(':')
    if len(parts) < 3:
        raise ValueError("Formato RTTTL inválido. Deve conter nome:config:notas")

    # title = parts[0].strip()
    settings = parts[1].strip().lower().split(',')
    notes_str = parts[2].strip()

    # Defaults
    default_duration = 4
    default_octave = 6
    bpm = 63

    for setting in settings:
        s = setting.strip()
        if s.startswith('d='):
            default_duration = int(s[2:])
        elif s.startswith('o='):
            default_octave = int(s[2:])
        elif s.startswith('b='):
            bpm = int(s[2:])

    # Duração de uma semibreve inteira (em milissegundos) com base no BPM
    # Uma semínima = (60 / bpm) segundos. Semibreve = 4 * (60 / bpm) * 1000 ms.
    whole_note_ms = (240000.0 / bpm)

    melody = []
    # Divide as notas por vírgula
    raw_notes = notes_str.split(',')
    for n in raw_notes:
        n = n.strip().lower()
        if not n:
            continue

        # Regex para parsear: [duracao][nota][#][_][oitava][ponto]
        match = re.match(r'^(\d+)?([a-g|p])(#)?(\.)?(\d+)?(\.)?$', n)
        if not match:
            continue

        dur_str, note_letter, sharp, dot1, oct_str, dot2 = match.groups()

        # Duração
        dur_val = int(dur_str) if dur_str else default_duration
        note_ms = whole_note_ms / dur_val

        # Ponto de aumento
        if dot1 or dot2:
            note_ms *= 1.5

        # Pausa
        if note_letter == 'p':
            melody.append((0, int(note_ms)))
            continue

        # Oitava
        oct_val = int(oct_str) if oct_str else default_octave

        # Nota final
        note_name = note_letter.upper()
        if sharp:
            note_name += 'S'
        note_name += str(oct_val)

        freq = NOTE_FREQS.get(note_name, 0)
        melody.append((freq, int(note_ms)))

    return melody


# Biblioteca de Músicas Clássicas para Buzzer (RTTTL)
SONG_CATALOG = {
    "Super Mario Bros (Tema)": (
        "SuperMario:d=4,o=5,b=100:16e6,16e6,32p,8e6,16c6,8e6,8g6,8p,8g,8p,"
        "8c6,16p,8g,16p,8e,16p,8a,8b,16a#,8a,16g.,16e6,16g6,8a6,16f6,8g6,"
        "8e6,16c6,16d6,8b,16p,8c6,16p,8g,16p,8e,16p,8a,8b,16a#,8a,16g.,"
        "16e6,16g6,8a6,16f6,8g6,8e6,16c6,16d6,8b"
    ),

    "Star Wars (Marcha Imperial)": (
        "Imperial:d=4,o=5,b=100:e,e,e,8c,16g,e,8c,16g,2e,b,b,b,8c6,16g,d#,"
        "8c,16g,2e,e6,8e,16e,e6,8d#6,16d6,16c#6,16c6,16c#6,8p,8f,a#,8a,"
        "16g#,16g,16f#,16g,8p,8c,d#,8c,16d#,g,8c,16g,2b"
    ),

    "Tetris (Korobeiniki)": (
        "Tetris:d=4,o=5,b=160:e6,8b,8c6,8d6,16e6,16d6,8c6,8b,a,8a,8c6,e6,8d6,8c6,"
        "b,8b,8c6,d6,e6,c6,a,2a,8p,d6,8f6,a6,8g6,8f6,e6,8e6,8c6,e6,8d6,8c6,"
        "b,8b,8c6,d6,e6,c6,a,a"
    ),

    "Megalovania (Undertale)": (
        "Megalovania:d=4,o=5,b=120:16d,16d,8d6,8a,8p,8g#,8g,8f,16d,16f,16g,"
        "16c,16c,8d6,8a,8p,8g#,8g,8f,16d,16f,16g,"
        "16b4,16b4,8d6,8a,8p,8g#,8g,8f,16d,16f,16g,"
        "16a#4,16a#4,8d6,8a,8p,8g#,8g,8f,16d,16f,16g"
    ),

    "Doom E1M1 (At Doom's Gate)": (
        "DoomE1M1:d=4,o=4,b=140:16e,16e,8e5,16e,16e,8d5,16e,16e,8c5,16e,16e,8a#,"
        "16e,16e,8b,16e,16e,8c5,16e,16e,8e5,16e,16e,8d5,16e,16e,8c5,16e,16e,4a#"
    ),

    "Astronomia (Coffin Dance)": (
        "CoffinDance:d=4,o=5,b=130:8g,8g,8g,8g,8a#,8a#,8a#,8a#,8d6,8d6,8d6,8d6,"
        "8c6,8c6,8c6,8c6,8f6,8f6,8f6,8f6,8d#6,8d#6,8d6,8d6,8c6,8c6,8a#,8a#,8g,8g"
    ),

    "A Pantera Cor-de-Rosa": (
        "PinkPanther:d=4,o=5,b=120:8d#,8e,2p,8f#,8g,2p,8d#,8e,16p,8f#,8g,"
        "16p,8c6,8b,16p,8d#,8e,16p,8b,2a#,2p,8a,8g,8e,8d,2e"
    ),

    "The Legend of Zelda": (
        "Zelda:d=4,o=5,b=125:a#4,8f4,16p,16a#4,8a#4,16c,16d,16d#,2f,8p,8f,"
        "16f,16f#,16g#,2a#,8p,8a#,16a#,16g#,16f#,8g#,16f#,2f,2d#,8d#,16f,"
        "8f#,2f,8d#,8c#,8c,2d,2f"
    ),

    "Harry Potter (Hedwig's Theme)": (
        "HarryPotter:d=4,o=5,b=125:8b,4e6,8g6,8f#6,4e6,8b6,4a6,2f#6,4e6,8g6,"
        "8f#6,4d6,8f6,2b,8b,4e6,8g6,8f#6,4e6,8b6,4d7,8c#7,4c7,8g#6,4c7,8b6,"
        "8a#6,4f#6,8g6,2e6"
    ),

    "Mortal Kombat": (
        "MortalKombat:d=4,o=5,b=135:8a4,8a4,8c,8a4,8d,8a4,8e,8d,8c,8c,8e,8c,"
        "8g,8c,8e,8c,8g4,8g4,8b4,8g4,8c,8g4,8d,8c,8f4,8f4,8a4,8f4,8c,8f4,8c,8b4"
    ),

    "Pac-Man Intro": (
        "PacMan:d=4,o=5,b=120:16b,16b6,16f#6,16d#6,16b6,32f#6,16d#6,8p,16c,"
        "16c7,16g6,16e6,16c7,32g6,16e6,8p,16b,16b6,16f#6,16d#6,16b6,32f#6,"
        "16d#6,8p,32d#6,32e6,32f6,32f6,32f#6,32g6,32g#6,32a6,8b6"
    ),

    "Nokia Gran Vals": (
        "NokiaTune:d=4,o=5,b=180:8e6,8d6,4f#,4g#,8c#6,8b,4d,4e,8b,8a,4c#,4e,2a"
    ),

    "Never Gonna Give You Up (Rickroll)": (
        "RickRoll:d=4,o=5,b=115:16c,16d,16f,16d,8a,8p,8a,8p,4g,8p,16c,16d,16f,"
        "16d,8g,8p,8g,8p,4f,16e,16d,16c,16d,16f,16d,8f,8g,8e,16d,8c,8c,8g,"
        "4f,2p"
    ),

    "Plants vs. Zombies - Loonboon (Boliche de Noz)": (
        "Loonboon:d=4,o=5,b=175:"
        "16g#,16b,16c#6,16d#6,8e6,8d#6,8c#6,8b,"
        "16g#,16b,16c#6,16d#6,4e6,4d#6,"
        "16g#,16b,16c#6,16d#6,8e6,8d#6,8c#6,8b,"
        "16f#,16a#,16c#6,16d#6,4d#6,4c#6,"
        "16g#,16b,16c#6,16d#6,8e6,8d#6,8c#6,8b,"
        "16g#,16b,16c#6,16d#6,4e6,4d#6,"
        "8b,8a#,8g#,8f#,8e,8d#,8c#,8d#,"
        "8e,8f#,4a#,2g#,"
        "16g#,16b,16d#6,16g#6,16f#6,16e6,16d#6,16c#6,"
        "16b,16a#,16g#,16f#,8g#,8g#,"
        "16e,16g#,16b,16e6,16d#6,16c#6,16b,16a#,"
        "16g#,16f#,16e,16d#,8e,8e,"
        "16d#,16f#,16a#,16d#6,16c#6,16b,16a#,16g#,"
        "16f#,16e,16d#,16c#,8d#,8d#,"
        "16g#,16b,16d#6,16g#6,16b6,16a#6,16g#6,16f#6,2g#6"
    ),

    "Plants vs. Zombies - Grasswalk (Tema Principal do Dia)": (
        "Grasswalk:d=4,o=5,b=125:"
        "8e,8g,8b,4b,8e,8g,8b,4b,"
        "8f#,8a,8c#6,4c#6,8f#,8a,8c#6,4c#6,"
        "4e6,8d6,8c6,4b,8g,8a,2b,"
        "4e6,8d6,8c6,4b,8g,8a,2f#,"
        "4e6,8d6,8c6,4b,8g,8a,4b,4d6,2c6,2b"
    ),

    "Plants vs. Zombies - Brainiac Maniac (Dr. Zomboss)": (
        "BrainiacManiac:d=4,o=5,b=165:"
        "16a,16a,8c6,16a,16a,8d6,16a,16a,8d#6,16a,16a,8e6,"
        "16a,16a,8g6,16a,16a,8f#6,16a,16a,8f6,16a,16a,8e6,"
        "8a,8c6,8e6,8a6,8g#6,8g6,8f#6,8f6,"
        "4e6,8d#6,8d6,4c#6,2c6"
    )
}

def get_song_notes(song_name: str) -> list:
    """Retorna a lista de (freq, duracao) para a música escolhida"""
    if song_name in SONG_CATALOG:
        return parse_rtttl(SONG_CATALOG[song_name])
    return []
