#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void *Z_Malloc(int size, int tag, void *user) { return malloc(size); }
void Z_Free(void *ptr) { free(ptr); }
void *I_Realloc(void *ptr, size_t size) { return realloc(ptr, size); }
FILE *M_fopen(const char *path, const char *mode) { return fopen(path, mode); }

#include "src/doomtype.h"
#include "src/memio.h"
#include "src/midifile.h"
#include "src/mus2mid.h"

int main(int argc, char **argv)
{
    FILE *f = fopen("../doom_buzzer/test_e1m1.mus", "rb");
    if (!f) { printf("Failed to open test_e1m1.mus\n"); return 1; }
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    byte *data = malloc(len);
    fread(data, 1, len, f);
    fclose(f);

    printf("Read %ld bytes of MUS data\n", len);

    MEMFILE *in = mem_fopen_read(data, len);
    MEMFILE *out = mem_fopen_write();
    int res = mus2mid(in, out);
    printf("mus2mid result: %d (0 = success)\n", res);

    void *outbuf;
    size_t outlen;
    mem_get_buf(out, &outbuf, &outlen);
    printf("MIDI size: %zu bytes\n", outlen);

    FILE *mid = fopen("../doom_buzzer/test_e1m1.mid", "wb");
    fwrite(outbuf, 1, outlen, mid);
    fclose(mid);

    midi_file_t *mf = MIDI_LoadFile("../doom_buzzer/test_e1m1.mid");
    if (!mf) {
        printf("MIDI_LoadFile failed!\n");
        return 1;
    }
    printf("MIDI_LoadFile succeeded! Tracks: %u, Division: %u\n",
           MIDI_NumTracks(mf), MIDI_GetFileTimeDivision(mf));

    midi_track_iter_t *iter = MIDI_IterateTrack(mf, 0);
    midi_event_t *ev;
    int notes = 0;
    while (MIDI_GetNextEvent(iter, &ev)) {
        if (ev->event_type == MIDI_EVENT_NOTE_ON && ev->data.channel.param2 > 0) {
            notes++;
            if (notes <= 15) {
                printf("  Note ON: ch=%u note=%u vel=%u delta=%u\n",
                       ev->data.channel.channel, ev->data.channel.param1,
                       ev->data.channel.param2, ev->delta_time);
            }
        }
    }
    printf("Total Note ON events: %d\n", notes);
    MIDI_FreeIterator(iter);
    MIDI_FreeFile(mf);

    return 0;
}
