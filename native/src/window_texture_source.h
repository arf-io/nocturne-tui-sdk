#ifndef NR_WINDOW_TEXTURE_SOURCE_H
#define NR_WINDOW_TEXTURE_SOURCE_H

#include <stdint.h>

typedef struct {
    double x, y, z, u, v, opacity;
} NrWindowTextureVertex;

/* Shape order is the RC2 WINDOW_SHAPES order, 0 through 9. */
int nrWindowTextureShapeContains(uint32_t shape, double u, double v);

/*
 * Composite one RC2 window-texture triangle. Cell arrays have four uint32_t
 * words per cell: glyph, foreground RGB, background RGB, hit id. `depth` has
 * one double per surface cell. All storage belongs to the caller and its
 * capacities are trusted after dimensions are checked for arithmetic overflow.
 * Clip coordinates are half-open and must lie within the surface dimensions.
 * Returns 0 on success/no-op and -1 on invalid inputs or non-finite derived
 * geometry. Byte-span and derived-arithmetic checks complete before drawing;
 * invalid calls do not mutate either output array.
 */
int nrWindowTextureTriangle(const NrWindowTextureVertex vertices[3],
                            uint32_t shape, uint32_t iris, double visibility,
                            uint32_t hitId, uint32_t textureWidth,
                            uint32_t textureHeight, const uint32_t *textureCells4,
                            uint32_t surfaceWidth, uint32_t surfaceHeight,
                            uint32_t clipX0, uint32_t clipY0,
                            uint32_t clipX1, uint32_t clipY1,
                            uint32_t *surfaceCells4, double *depth);

#endif
