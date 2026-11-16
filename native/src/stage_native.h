#ifndef NOCTURNE_STAGE_NATIVE_H
#define NOCTURNE_STAGE_NATIVE_H

#include "nocturne_native.h"
#include <stdint.h>

enum {
    NR_SOURCE_STAGE_COMPONENT_CAPACITY = 512,
    NR_SOURCE_STAGE_TEXT_CAPACITY = 32768,
    NR_SOURCE_STAGE_DATA_CAPACITY = 16384,
    NR_SOURCE_STAGE_NODE_WORDS = 32
};

/* `id` is the current SDK retained identity; node[1] remains the independent
 * original source legacyFlags word. materialId is 0 when unlinked, otherwise
 * the 1-based public material ID used for opt-in alpha/pattern sampling. */
typedef struct {
    uint32_t used;
    uint32_t id;
    uint32_t materialId;
    uint32_t reserved;
    int32_t node[NR_SOURCE_STAGE_NODE_WORDS];
} SourceStageComponentRecord;

/* Ordered source records share lossless scalar/data pools. Each original node
 * retains its exact 32 words; words 17..20 point into these pools. The count
 * limits are the recovered RC2 source ABI, independent of viewport size. */
typedef struct {
    uint32_t count;
    uint32_t textCount;
    uint32_t dataCount;
    uint32_t reserved;
    SourceStageComponentRecord components[NR_SOURCE_STAGE_COMPONENT_CAPACITY];
    uint32_t text[NR_SOURCE_STAGE_TEXT_CAPACITY];
    int32_t data[NR_SOURCE_STAGE_DATA_CAPACITY];
} SourceStageState;

/* Epoch91: original Stage composition, no pointers or duplicate node pool. */
typedef struct {
 uint32_t enabled,eventCount;
 uint64_t timeMs;
 int32_t values[64];
 uint32_t palette[32],starPalette[32],glyphs[32],novaGlyphs[16];
 int32_t events[128][8];
} SourceStageScene;

/* One-shot adapter for current presentation components that need the exact
 * source Stage paint path without retained source-stage storage. `text` is the
 * full offset-addressable scalar pool named by node[17:19]. The caller owns
 * hitId and semanticOwner; the helper uses current view time/background and
 * writes through the normal shared cell buffer. */
int nrSourceStageDrawTransient(NrContext *context, const int32_t node[32],
                              const uint32_t *text, uint32_t textCount,
                              uint32_t semanticOwner, uint32_t hitId);

#endif
