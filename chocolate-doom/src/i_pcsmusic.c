//
// PC Speaker Music Module - Reproduz a trilha sonora diretamente no BUZZER!
// Desenvolvido para tocar a trilha sonora de DOOM via porta 0x61 / PIT 8254.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "doomtype.h"
#include "i_sound.h"
#include "pcsound.h"
#include "midifile.h"
#include "mus2mid.h"
#include "memio.h"
#include "m_misc.h"
#include "z_zone.h"
#include "SDL.h"
#include "SDL_thread.h"

static boolean music_initialized = false;
static boolean music_playing = false;
static boolean music_paused = false;
static int music_volume = 127;

static SDL_Thread *player_thread = NULL;
static volatile boolean thread_exit_requested = false;
static midi_file_t *current_song = NULL;
static boolean song_looping = false;

static void I_PCS_StopSong(void);

#define MAX_ACTIVE_NOTES 64

typedef struct
{
    int note;
    int channel;
} active_note_t;

static active_note_t active_notes[MAX_ACTIVE_NOTES];
static int num_active_notes = 0;

static void RecalculatePitch(void)
{
    int highest_note = -1;
    int i;

    if (music_paused || music_volume <= 0 || num_active_notes <= 0)
    {
        pcs_music_freq = 0;
        return;
    }

    // Prioridade na nota mais alta (top-note priority) para destacar a melodia/riff de DOOM
    for (i = 0; i < num_active_notes; i++)
    {
        if (active_notes[i].note > highest_note)
        {
            highest_note = active_notes[i].note;
        }
    }

    if (highest_note > 0)
    {
        // Fórmula padrão MIDI -> Frequência em Hz: 440 * 2^((note - 69) / 12)
        double freq_d = 440.0 * pow(2.0, (highest_note - 69.0) / 12.0);
        int freq = (int)(freq_d + 0.5);
        if (freq >= 20 && freq <= 15000)
        {
            pcs_music_freq = freq;
            return;
        }
    }

    pcs_music_freq = 0;
}

static void AddActiveNote(int note, int channel)
{
    int i;
    for (i = 0; i < num_active_notes; i++)
    {
        if (active_notes[i].note == note && active_notes[i].channel == channel)
        {
            return;
        }
    }
    if (num_active_notes < MAX_ACTIVE_NOTES)
    {
        active_notes[num_active_notes].note = note;
        active_notes[num_active_notes].channel = channel;
        num_active_notes++;
    }
    RecalculatePitch();
}

static void RemoveActiveNote(int note, int channel)
{
    int i, j;
    for (i = 0; i < num_active_notes; i++)
    {
        if (active_notes[i].note == note && active_notes[i].channel == channel)
        {
            for (j = i; j < num_active_notes - 1; j++)
            {
                active_notes[j] = active_notes[j + 1];
            }
            num_active_notes--;
            break;
        }
    }
    RecalculatePitch();
}

static void ClearActiveNotes(void)
{
    num_active_notes = 0;
    pcs_music_freq = 0;
}

static boolean IsMid(byte *mem, int len)
{
    return len > 4 && !memcmp(mem, "MThd", 4);
}

static boolean ConvertMus(byte *musdata, int len, const char *filename)
{
    MEMFILE *instream = mem_fopen_read(musdata, len);
    MEMFILE *outstream = mem_fopen_write();
    void *outbuf;
    size_t outbuf_len;
    int result;

    result = mus2mid(instream, outstream);
    if (result == 0)
    {
        mem_get_buf(outstream, &outbuf, &outbuf_len);
        M_WriteFile(filename, outbuf, outbuf_len);
    }

    mem_fclose(instream);
    mem_fclose(outstream);
    return (result == 0);
}

static int MusicPlayerThread(void *arg)
{
    midi_file_t *file = (midi_file_t *)arg;
    unsigned int num_tracks;
    unsigned int time_division;
    midi_track_iter_t **iters;
    midi_event_t **track_event;
    uint64_t *track_time;
    int *active;
    unsigned int i;
    uint64_t current_tick = 0;
    uint32_t us_per_beat = 500000; // 120 bpm default
    uint64_t target_tick_us = 0;
    uint64_t perf_freq = SDL_GetPerformanceFrequency();
    uint64_t start_perf = SDL_GetPerformanceCounter();

    if (file == NULL)
    {
        return 0;
    }

    num_tracks = MIDI_NumTracks(file);
    time_division = MIDI_GetFileTimeDivision(file);
    if (time_division == 0)
    {
        time_division = 96;
    }

    iters = malloc(num_tracks * sizeof(midi_track_iter_t *));
    track_event = malloc(num_tracks * sizeof(midi_event_t *));
    track_time = malloc(num_tracks * sizeof(uint64_t));
    active = malloc(num_tracks * sizeof(int));

    for (i = 0; i < num_tracks; i++)
    {
        iters[i] = MIDI_IterateTrack(file, i);
        if (MIDI_GetNextEvent(iters[i], &track_event[i]))
        {
            track_time[i] = track_event[i]->delta_time;
            active[i] = 1;
        }
        else
        {
            active[i] = 0;
        }
    }

    ClearActiveNotes();

    while (!thread_exit_requested)
    {
        int min_track = -1;
        uint64_t min_time = (uint64_t)-1;
        midi_event_t *ev;

        if (music_paused)
        {
            pcs_music_freq = 0;
            SDL_Delay(50);
            start_perf = SDL_GetPerformanceCounter() - ((target_tick_us * perf_freq) / 1000000);
            continue;
        }

        // Encontra o proximo evento com menor delta_time
        for (i = 0; i < num_tracks; i++)
        {
            if (active[i] && track_time[i] < min_time)
            {
                min_time = track_time[i];
                min_track = i;
            }
        }

        if (min_track == -1)
        {
            ClearActiveNotes();
            if (song_looping)
            {
                // Reinicia a musica do comeco
                for (i = 0; i < num_tracks; i++)
                {
                    MIDI_RestartIterator(iters[i]);
                    if (MIDI_GetNextEvent(iters[i], &track_event[i]))
                    {
                        track_time[i] = track_event[i]->delta_time;
                        active[i] = 1;
                    }
                    else
                    {
                        active[i] = 0;
                    }
                }
                current_tick = 0;
                target_tick_us = 0;
                start_perf = SDL_GetPerformanceCounter();
                continue;
            }
            else
            {
                break;
            }
        }

        // Aguarda com precisao de microsegundos ate o momento do proximo evento
        if (min_time > current_tick)
        {
            uint64_t delta_ticks = min_time - current_tick;
            uint64_t step_us = (delta_ticks * (uint64_t)us_per_beat) / time_division;
            target_tick_us += step_us;

            for (;;)
            {
                uint64_t now_perf;
                uint64_t elapsed_us;
                uint64_t rem_us;

                if (thread_exit_requested)
                    break;

                if (music_paused)
                {
                    pcs_music_freq = 0;
                    SDL_Delay(50);
                    start_perf = SDL_GetPerformanceCounter() - ((target_tick_us * perf_freq) / 1000000);
                    continue;
                }

                now_perf = SDL_GetPerformanceCounter();
                elapsed_us = ((now_perf - start_perf) * 1000000) / perf_freq;

                if (elapsed_us >= target_tick_us)
                    break;

                rem_us = target_tick_us - elapsed_us;
                if (rem_us > 2500)
                {
                    SDL_Delay((Uint32)(rem_us / 1000 - 1));
                }
                else
                {
                    SDL_Delay(0);
                }
            }

            current_tick = min_time;
        }

        if (thread_exit_requested)
        {
            break;
        }

        // Processa o evento MIDI
        ev = track_event[min_track];
        if (ev != NULL)
        {
            if (ev->event_type == MIDI_EVENT_META && ev->data.meta.type == MIDI_META_SET_TEMPO)
            {
                if (ev->data.meta.length == 3 && ev->data.meta.data != NULL)
                {
                    byte *d = ev->data.meta.data;
                    us_per_beat = (d[0] << 16) | (d[1] << 8) | d[2];
                    if (us_per_beat < 10000)
                    {
                        us_per_beat = 500000;
                    }
                }
            }
            else if (ev->event_type == MIDI_EVENT_NOTE_ON && ev->data.channel.param2 > 0)
            {
                // Ignora canal 9 (percussao/bateria) para focar no baixo e guitarra/melodia
                if (ev->data.channel.channel != 9)
                {
                    AddActiveNote((int)ev->data.channel.param1, (int)ev->data.channel.channel);
                }
            }
            else if (ev->event_type == MIDI_EVENT_NOTE_OFF ||
                    (ev->event_type == MIDI_EVENT_NOTE_ON && ev->data.channel.param2 == 0))
            {
                if (ev->data.channel.channel != 9)
                {
                    RemoveActiveNote((int)ev->data.channel.param1, (int)ev->data.channel.channel);
                }
            }
            else if (ev->event_type == MIDI_EVENT_CONTROLLER)
            {
                if (ev->data.channel.param1 == MIDI_CONTROLLER_ALL_NOTES_OFF ||
                    ev->data.channel.param1 == MIDI_CONTROLLER_ALL_SOUND_OFF)
                {
                    ClearActiveNotes();
                }
            }
        }

        // Avanca para o proximo evento do track
        if (MIDI_GetNextEvent(iters[min_track], &track_event[min_track]))
        {
            track_time[min_track] += track_event[min_track]->delta_time;
        }
        else
        {
            active[min_track] = 0;
        }
    }

    ClearActiveNotes();

    for (i = 0; i < num_tracks; i++)
    {
        MIDI_FreeIterator(iters[i]);
    }

    free(iters);
    free(track_event);
    free(track_time);
    free(active);

    return 0;
}

static boolean I_PCS_Music_Init(void)
{
    music_initialized = true;
    music_playing = false;
    music_paused = false;
    ClearActiveNotes();

    return true;
}

static void I_PCS_StopSong(void)
{
    thread_exit_requested = true;
    music_playing = false;
    ClearActiveNotes();

    if (player_thread != NULL)
    {
        SDL_WaitThread(player_thread, NULL);
        player_thread = NULL;
    }

    current_song = NULL;
}

static void I_PCS_Music_Shutdown(void)
{
    I_PCS_StopSong();
    music_initialized = false;
}

static void I_PCS_Music_SetMusicVolume(int volume)
{
    music_volume = volume;
    RecalculatePitch();
}

static void I_PCS_Music_PauseMusic(void)
{
    music_paused = true;
    pcs_music_freq = 0;
}

static void I_PCS_Music_ResumeMusic(void)
{
    music_paused = false;
    RecalculatePitch();
}

static void *I_PCS_Music_RegisterSong(void *data, int len)
{
    const char *filename = "doom_pcsmus.mid";
    midi_file_t *file;

    if (!music_initialized)
    {
        return NULL;
    }

    if (IsMid((byte *)data, len))
    {
        M_WriteFile(filename, data, len);
    }
    else
    {
        ConvertMus((byte *)data, len, filename);
    }

    file = MIDI_LoadFile((char *)filename);
    M_remove(filename);

    return file;
}

static void I_PCS_Music_UnRegisterSong(void *handle)
{
    if (handle != NULL)
    {
        if (current_song == handle)
        {
            I_PCS_StopSong();
        }
        MIDI_FreeFile((midi_file_t *)handle);
    }
}

static void I_PCS_Music_PlaySong(void *handle, boolean looping)
{
    I_PCS_StopSong();

    if (!music_initialized || handle == NULL)
    {
        return;
    }

    current_song = (midi_file_t *)handle;
    song_looping = looping;
    thread_exit_requested = false;
    music_playing = true;
    music_paused = false;

    player_thread = SDL_CreateThread(MusicPlayerThread, "PC speaker music thread", current_song);
}

static boolean I_PCS_Music_MusicIsPlaying(void)
{
    return music_playing;
}

static const snddevice_t music_pcsound_devices[] =
{
    SNDDEVICE_PCSPEAKER,
    SNDDEVICE_SB,
    SNDDEVICE_GENMIDI,
    SNDDEVICE_ADLIB,
    SNDDEVICE_SOUNDCANVAS,
    SNDDEVICE_GUS,
    SNDDEVICE_AWE32,
    SNDDEVICE_PAS,
    SNDDEVICE_WAVEBLASTER,
};

const music_module_t music_pcsound_module =
{
    music_pcsound_devices,
    arrlen(music_pcsound_devices),
    I_PCS_Music_Init,
    I_PCS_Music_Shutdown,
    I_PCS_Music_SetMusicVolume,
    I_PCS_Music_PauseMusic,
    I_PCS_Music_ResumeMusic,
    I_PCS_Music_RegisterSong,
    I_PCS_Music_UnRegisterSong,
    I_PCS_Music_PlaySong,
    I_PCS_StopSong,
    I_PCS_Music_MusicIsPlaying,
    NULL, // Poll
};
