#ifndef NR_WINDOW_TEXTURE_H
#define NR_WINDOW_TEXTURE_H
#include "nocturne_native.h"
#include <stdint.h>

enum { NR_WINDOW_TEXTURE_CELLS = 65536 };
typedef struct { uint32_t width,height,offset,reserved; } WindowTextureRecord;
typedef struct {
    uint32_t count,reserved;
    WindowTextureRecord windows[NR_MAX_WINDOWS];
    uint32_t cells[NR_WINDOW_TEXTURE_CELLS][4];
} WindowTextures;
/* Exact historical texture pool prefix; current descriptors are appended. */
typedef struct {
    uint32_t count,reserved;
    WindowTextureRecord windows[12];
    uint32_t cells[NR_WINDOW_TEXTURE_CELLS][4];
} LegacyWindowTextures;
#endif
