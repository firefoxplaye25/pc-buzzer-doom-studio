//
// Copyright(C) 2005-2014 Simon Howard
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// DESCRIPTION:
//    PC speaker interface - Conectado ao Hardware Buzzer / Porta 0x61.
//

#ifdef _WIN32

#include "SDL.h"
#include "SDL_thread.h"
#include <windows.h>
#include <mmsystem.h>
#include <stdio.h>

#include "pcsound.h"
#include "pcsound_internal.h"

typedef int (__stdcall *InitializeOls_t)(void);
typedef void (__stdcall *DeinitializeOls_t)(void);
typedef void (__stdcall *WriteIoPortByte_t)(unsigned short, unsigned char);
typedef unsigned char (__stdcall *ReadIoPortByte_t)(unsigned short);

static HMODULE hWinRing0 = NULL;
static InitializeOls_t pInitializeOls = NULL;
static DeinitializeOls_t pDeinitializeOls = NULL;
static WriteIoPortByte_t pWriteIoPortByte = NULL;
static ReadIoPortByte_t pReadIoPortByte = NULL;
static int winring0_active = 0;

static SDL_Thread *sound_thread_handle;
static int sound_thread_running;
static pcsound_callback_func callback = NULL;

void PCSound_Win32_SetCallback(pcsound_callback_func callback_func)
{
    callback = callback_func;
}

static int SoundThread(void *unused)
{
    int frequency;
    int duration;
    int speaker_on = 0;
    int last_freq = -1;
    LARGE_INTEGER perf_freq, t_start, t_now;
    
    timeBeginPeriod(1);
    QueryPerformanceFrequency(&perf_freq);

    while (sound_thread_running)
    {
        if (callback != NULL)
        {
            callback(&duration, &frequency);
        }
        else
        {
            duration = 1000 / 140;
            frequency = 0;
        }

        // SFX (tiros, portas, monstros, itens) tem prioridade no Buzzer.
        // Quando nao ha SFX tocando, a musica do DOOM toca no Buzzer!
        int active_freq = 0;
        if (frequency > 0 && frequency < 20000)
        {
            active_freq = frequency;
        }
        else if (pcs_music_freq > 0 && pcs_music_freq < 20000)
        {
            active_freq = pcs_music_freq;
        }

        if (winring0_active && pWriteIoPortByte && pReadIoPortByte)
        {
            if (active_freq > 0)
            {
                if (active_freq != last_freq)
                {
                    unsigned short divisor = (unsigned short)(1193180 / active_freq);
                    // PIT 8254 Channel 2 (Square Wave Mode 3)
                    pWriteIoPortByte(0x43, 0xB6);
                    pWriteIoPortByte(0x42, (unsigned char)(divisor & 0xFF));
                    pWriteIoPortByte(0x42, (unsigned char)((divisor >> 8) & 0xFF));
                    last_freq = active_freq;
                }

                if (!speaker_on)
                {
                    unsigned char ctrl = pReadIoPortByte(0x61);
                    pWriteIoPortByte(0x61, (unsigned char)(ctrl | 0x03));
                    speaker_on = 1;
                }
            }
            else
            {
                if (speaker_on)
                {
                    unsigned char ctrl = pReadIoPortByte(0x61);
                    pWriteIoPortByte(0x61, (unsigned char)(ctrl & 0xFC));
                    speaker_on = 0;
                    last_freq = -1;
                }
            }

            // Aguarda a duracao exata de cada tick do som (ex: 7ms a 140Hz)
            if (duration > 0)
            {
                QueryPerformanceCounter(&t_start);
                double target_sec = (double)duration / 1000.0;
                for (;;)
                {
                    QueryPerformanceCounter(&t_now);
                    double elapsed = (double)(t_now.QuadPart - t_start.QuadPart) / (double)perf_freq.QuadPart;
                    if (elapsed >= target_sec)
                        break;
                    if (target_sec - elapsed > 0.002)
                        Sleep(1);
                    else
                        Sleep(0);
                }
            }
        }
        else
        {
            // Fallback usando Beep da API do Windows caso WinRing0 nao esteja ativo
            if (active_freq > 0)
            {
                Beep(active_freq, duration > 0 ? duration : 7);
            }
            else if (duration > 0)
            {
                Sleep(duration);
            }
        }
    }

    if (speaker_on && winring0_active && pWriteIoPortByte && pReadIoPortByte)
    {
        unsigned char ctrl = pReadIoPortByte(0x61);
        pWriteIoPortByte(0x61, (unsigned char)(ctrl & 0xFC));
    }
    timeEndPeriod(1);
    
    return 0;    
}

static int PCSound_Win32_Init(pcsound_callback_func callback_func)
{
    // Tenta carregar o driver direto da placa-mãe (WinRing0x64.dll)
    hWinRing0 = LoadLibraryA("WinRing0x64.dll");
    if (!hWinRing0)
    {
        hWinRing0 = LoadLibraryA("pc_beeper\\WinRing0x64.dll");
    }
    if (!hWinRing0)
    {
        hWinRing0 = LoadLibraryA("..\\WinRing0x64.dll");
    }

    if (hWinRing0)
    {
        pInitializeOls = (InitializeOls_t)GetProcAddress(hWinRing0, "InitializeOls");
        pDeinitializeOls = (DeinitializeOls_t)GetProcAddress(hWinRing0, "DeinitializeOls");
        pWriteIoPortByte = (WriteIoPortByte_t)GetProcAddress(hWinRing0, "WriteIoPortByte");
        pReadIoPortByte = (ReadIoPortByte_t)GetProcAddress(hWinRing0, "ReadIoPortByte");

        if (pInitializeOls && pInitializeOls() != 0)
        {
            winring0_active = 1;
            printf("\n>>> [DOOM BUZZER] Hardware Buzzer ATIVO na Porta 0x61 via WinRing0! <<<\n\n");
        }
        else
        {
            printf("\n[DOOM BUZZER] WinRing0 nao inicializado como Admin, usando Beep() do Windows.\n");
        }
    }
    else
    {
        printf("\n[DOOM BUZZER] WinRing0x64.dll nao encontrada, usando Beep() padrao.\n");
    }

    // Inicia a thread de som do PC Speaker
    callback = callback_func;
    sound_thread_running = 1;

    sound_thread_handle =
        SDL_CreateThread(SoundThread, "PC speaker thread", NULL);

    return 1;
}

static void PCSound_Win32_Shutdown(void)
{
    sound_thread_running = 0;
    if (sound_thread_handle)
    {
        SDL_WaitThread(sound_thread_handle, NULL);
        sound_thread_handle = NULL;
    }

    if (winring0_active && pWriteIoPortByte && pReadIoPortByte)
    {
        unsigned char ctrl = pReadIoPortByte(0x61);
        pWriteIoPortByte(0x61, (unsigned char)(ctrl & 0xFC));
        if (pDeinitializeOls) pDeinitializeOls();
        winring0_active = 0;
    }

    if (hWinRing0)
    {
        FreeLibrary(hWinRing0);
        hWinRing0 = NULL;
    }
}

pcsound_driver_t pcsound_win32_driver = 
{
    "Windows",
    PCSound_Win32_Init,
    PCSound_Win32_Shutdown,
};

#endif /* #ifdef _WIN32 */
