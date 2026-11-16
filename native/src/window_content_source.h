#ifndef NR_WINDOW_CONTENT_SOURCE_H
#define NR_WINDOW_CONTENT_SOURCE_H

#include <stdint.h>

enum { NR_WINDOW_CONTENT_RAMP_CELLS = 2048, NR_WINDOW_CONTENT_WAVEFORM_SAMPLES = 128 };

typedef struct {
    uint32_t width;
    uint32_t height;
    uint32_t shape; /* nrWindowTextureShapeContains order, 0..9 */
    const uint32_t *titleScalars;
    uint32_t titleCount;
    const uint32_t *contentScalars;
    uint32_t contentCount;
    const uint32_t *labelScalars; /* complete footer label, rendered verbatim; <=76 UTF-16 units */
    uint32_t labelCount;
    double clockMs;
    uint32_t inkRgb;
    uint32_t backgroundRgb;
    uint32_t accentRgb;
    const uint32_t *ramp2048;
    double stopTotal;
    const double *waveform;
    uint32_t waveformCount;
    uint32_t *cells4; /* caller-owned [glyph, foreground, background, id] */
} NrWindowContentSource;

/* Returns 1 for a valid record and 0 for invalid pointers/domains/arithmetic,
 * matching the source-stage validator convention.
 * Text capacities follow the source UTF-16 limits (title 160, body 4096).
 * The output dimensions have minimum usable size 9x4 and otherwise follow
 * signed source-component and caller-buffer byte-span representation bounds. */
int nrWindowContentSourceValid(const NrWindowContentSource *source);

/* Paints the original generated texture into caller-owned cells4. Returns 0
 * on success and -1 on invalid input; invalid calls leave cells4 unchanged. */
int nrWindowContentSourceRender(const NrWindowContentSource *source);

#endif
