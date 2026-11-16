#ifndef NOCTURNE_SOURCE_STAGE_COMPONENTS_H
#define NOCTURNE_SOURCE_STAGE_COMPONENTS_H

#include "source_material_sampler.h"

#include <stdint.h>

enum {
    NR_SOURCE_STAGE_RULE = 2,
    NR_SOURCE_STAGE_PROGRESS = 6,
    NR_SOURCE_STAGE_PIE = 8,
    NR_SOURCE_STAGE_DONUT = 9,
    NR_SOURCE_STAGE_DIGITS = 12
};

enum {
    NR_SOURCE_CELL_GLYPH = 0,
    NR_SOURCE_CELL_FILL = 1,
    NR_SOURCE_CELL_FLATTEN = 2,
    NR_SOURCE_CELL_BACKGROUND_TINT = 3
};

typedef struct {
    uint32_t glyph;
    uint32_t foregroundRgb;
    uint32_t backgroundRgb;
    uint32_t legacyFlags;
    uint32_t semanticOwner;
} NrSourceStageCell;

/* The sink owns composition and semantic identity. sourceFgRgb is the authored
 * source color before sourceFgOpacity blending. The operation distinguishes
 * glyph replacement, fill, half-block flattening and background-only tint.
 * sourceBgRgb is meaningful only when backgroundExplicit is nonzero. A
 * nonzero legacyFlags carries the old
 * node ID; zero means preserve the destination flag as the source did when
 * node ID was zero. semanticOwner is supplied by the current caller and is
 * never inferred here.
 * Subcells are emitted in original row-major dot order. The last covered dot
 * in a terminal cell wins the source foreground exactly as rc.2 did; sinks
 * must not average those colors. */
typedef struct {
    void *context;
    int32_t frameWidth;
    int32_t frameHeight;
    int (*readCell)(void *context, int32_t x, int32_t y,
                    NrSourceStageCell *outCell);
    void (*cell)(void *context, int32_t x, int32_t y, uint32_t operation,
                 uint32_t glyph,
                 uint32_t sourceFgRgb, uint32_t sourceFgOpacity,
                 uint32_t sourceBgRgb, uint32_t sourceBgOpacity,
                 uint32_t backgroundExplicit,
                 uint32_t legacyFlags, uint32_t semanticOwner);
    void (*subcell)(void *context, int32_t x, int32_t y,
                    uint32_t subX, uint32_t subY, uint32_t sourceRgb,
                    uint32_t sourceOpacity, uint32_t coverage,
                    uint32_t legacyFlags, uint32_t semanticOwner);
} NrSourceStageComponentSink;

/* Input preserves the complete source record and authored arrays. timeMs uses
 * the source renderer's integer millisecond clock. material supplies exact
 * stPalette controls for pie/donut slices. baseColor supplies state-3 dimming.
 * Return 0 when applied, 1 for unsupported kind, and -1 for invalid input or
 * sink. Validation occurs before callbacks. Original node-domain limits are
 * scalar/palette domains remain source-compatible while geometry is allowed
 * through signed subcell-coordinate bounds; frame dimensions are host-owned
 * and are not capped to the old renderer viewport. */
typedef struct {
    int32_t node[32];
    const uint32_t *text;
    uint32_t textCount;
    const int32_t *data;
    uint32_t dataCount;
    uint64_t timeMs;
    const NrSourceMaterialSampler *material;
    uint32_t baseColor;
    uint32_t semanticOwner;
} NrSourceStageComponent;

int nrSourceStageComponentApply(const NrSourceStageComponent *component,
                                const NrSourceStageComponentSink *sink);
int nrSourceStageComponentValid(const NrSourceStageComponent *component,
                                int32_t frameWidth,int32_t frameHeight);

#endif
