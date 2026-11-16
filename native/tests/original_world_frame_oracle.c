/* Differential runner for the exact historical renderer in src/nocturne.c. */
#include "nocturne_world.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { MAX_CELLS = 120 * 40, MAX_LINE = 4096 };

static int read_expected(const char *path, const NsCell *cells, size_t bytes) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    unsigned char actual[MAX_CELLS * sizeof(NsCell)];
    size_t n = fread(actual, 1, sizeof(actual), f);
    int extra = fgetc(f);
    fclose(f);
    return n == bytes && extra == EOF && memcmp(actual, cells, bytes) == 0;
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: original_world_frame_oracle EVIDENCE_DIR\n"); return 2; }
    char tsvPath[1024];
    if (snprintf(tsvPath, sizeof(tsvPath), "%s/ORIGINAL-WORLD-FRAMES.tsv", argv[1]) >= (int)sizeof(tsvPath)) return 2;
    FILE *input = fopen(tsvPath, "r");
    if (!input) { perror(tsvPath); return 2; }
    NsCell cells[MAX_CELLS];
    uint32_t colors[MAX_CELLS * 8];
    int32_t depth[MAX_CELLS * 8];
    char line[MAX_LINE];
    unsigned count = 0;
    while (fgets(line, sizeof(line), input)) {
        char *save = NULL, *token = strtok_r(line, " \t\r\n", &save);
        if (!token) continue;
        char id[160];
        if (strlen(token) >= sizeof(id)) return 3;
        strcpy(id, token);
        token = strtok_r(NULL, " \t\r\n", &save);
        if (!token) return 3;
        errno = 0; uint64_t timeMs = strtoull(token, NULL, 10); if (errno) return 3;
        NsWorldConfig config; NsWorldDetail detail;
        int32_t *world = config.v, *details = detail.v;
        for (int i = 0; i < NSW_CONFIG_WORDS + NSW_DETAIL_WORDS; i++) {
            token = strtok_r(NULL, " \t\r\n", &save);
            if (!token) { fprintf(stderr, "%s: short scenario record\n", id); return 3; }
            errno = 0; long value = strtol(token, NULL, 10);
            if (errno || value < INT32_MIN || value > INT32_MAX) return 3;
            if (i < NSW_CONFIG_WORDS) world[i] = (int32_t)value;
            else details[i - NSW_CONFIG_WORDS] = (int32_t)value;
        }
        if (strtok_r(NULL, " \t\r\n", &save)) { fprintf(stderr, "%s: extra scenario fields\n", id); return 3; }
        uint32_t n = (uint32_t)world[NSW_WIDTH] * (uint32_t)world[NSW_HEIGHT];
        if (!n || n > MAX_CELLS) return 3;
        int32_t written = nsWorldRenderDetailed(&config, timeMs, &detail, cells, n, colors, depth, n * 8);
        if (written != (int32_t)n) { fprintf(stderr, "%s: original C renderer rejected scenario (%d)\n", id, written); return 4; }
        char cellsPath[1024];
        if (snprintf(cellsPath, sizeof(cellsPath), "%s/%s.cells", argv[1], id) >= (int)sizeof(cellsPath)) return 2;
        if (!read_expected(cellsPath, cells, (size_t)n * sizeof(NsCell))) {
            fprintf(stderr, "%s: original C output differs byte-for-byte from archived WASM\n", id);
            return 5;
        }
        count++;
    }
    fclose(input);
    if (count != 16) { fprintf(stderr, "expected 16 reference frames, compared %u\n", count); return 6; }
    puts("original C renderer: exact RC2 WASM cell frames matched (16 scenes/times/projections/sampling variants)");
    return 0;
}
