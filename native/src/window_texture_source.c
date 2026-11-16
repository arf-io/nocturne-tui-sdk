#include "window_texture_source.h"

#include <stddef.h>
#include <stdint.h>

#define NR_PI 3.14159265358979323846264338327950288
#define NR_TAU 6.28318530717958647692528676655900576

static int nrFinite(double value) {
    return value == value && value <= 1.7976931348623157e308 &&
           value >= -1.7976931348623157e308;
}

static double nrAbsValue(double value) { return value < 0.0 ? -value : value; }

static double nrFloorValue(double value) {
    int64_t integer = (int64_t)value;
    return (double)(integer - (value < (double)integer));
}

static double nrSinRadians(double value) {
    double turns, x, x2, term, sum;
    if (!nrFinite(value)) return 0.0;
    turns = nrFloorValue(value / NR_TAU + 0.5);
    x = value - turns * NR_TAU;
    x2 = x * x;
    term = x;
    sum = term;
    term *= -x2 / (2.0 * 3.0); sum += term;
    term *= -x2 / (4.0 * 5.0); sum += term;
    term *= -x2 / (6.0 * 7.0); sum += term;
    term *= -x2 / (8.0 * 9.0); sum += term;
    term *= -x2 / (10.0 * 11.0); sum += term;
    term *= -x2 / (12.0 * 13.0); sum += term;
    term *= -x2 / (14.0 * 15.0); sum += term;
    term *= -x2 / (16.0 * 17.0); sum += term;
    term *= -x2 / (18.0 * 19.0); sum += term;
    return sum;
}

static double nrCosRadians(double value) {
    double turns, x, x2, term, sum;
    if (!nrFinite(value)) return 0.0;
    turns = nrFloorValue(value / NR_TAU + 0.5);
    x = value - turns * NR_TAU;
    x2 = x * x;
    term = 1.0;
    sum = term;
    term *= -x2 / (1.0 * 2.0); sum += term;
    term *= -x2 / (3.0 * 4.0); sum += term;
    term *= -x2 / (5.0 * 6.0); sum += term;
    term *= -x2 / (7.0 * 8.0); sum += term;
    term *= -x2 / (9.0 * 10.0); sum += term;
    term *= -x2 / (11.0 * 12.0); sum += term;
    term *= -x2 / (13.0 * 14.0); sum += term;
    term *= -x2 / (15.0 * 16.0); sum += term;
    term *= -x2 / (17.0 * 18.0); sum += term;
    term *= -x2 / (19.0 * 20.0); sum += term;
    return sum;
}

static double nrSqrtValue(double value) {
    double estimate;
    uint32_t i;
    if (value <= 0.0) return 0.0;
    estimate = value >= 1.0 ? value : 1.0;
    for (i = 0; i < 24; ++i) estimate = (estimate + value / estimate) * 0.5;
    return estimate;
}

static int nrShapeValid(uint32_t shape) { return shape <= 9u; }

int nrWindowTextureShapeContains(uint32_t shape, double u, double v) {
    double x, y, dx, dy, radius, cosine, cosine2, cosine6;
    if (!nrShapeValid(shape) || !nrFinite(u + v) || u < 0.0 || u > 1.0 ||
        v < 0.0 || v > 1.0) return 0;
    x = nrAbsValue(u - 0.5) * 2.0;
    y = nrAbsValue(v - 0.5) * 2.0;
    switch (shape) {
        case 0: return 1;
        case 1: {
            double ax = x > 0.78 ? (x - 0.78) / 0.22 : 0.0;
            double ay = y > 0.65 ? (y - 0.65) / 0.35 : 0.0;
            return ax * ax + ay * ay <= 1.0;
        }
        case 2: return x * x + y * y <= 1.0;
        case 3: return x <= 1.0 - y * 0.32;
        case 4: return x + y <= 1.0;
        case 5:
            if (x < 0.5) return 1;
            dx = (x - 0.5) * 2.0;
            return dx * dx + y * y <= 1.0;
        case 6: return !((u < 0.075 || u > 0.925) && nrAbsValue(v - 0.5) < 0.14);
        case 7: return x * x * x * x + y * y * y * y <= 1.0;
        case 8:
            dx = u - 0.5;
            dy = v - 0.5;
            radius = nrSqrtValue(dx * dx + dy * dy);
            if (radius == 0.0) return 1;
            cosine = dx / radius;
            cosine2 = cosine * cosine;
            cosine6 = 32.0 * cosine2 * cosine2 * cosine2 -
                      48.0 * cosine2 * cosine2 + 18.0 * cosine2 - 1.0;
            return x * x + y * y <= 0.78 + 0.22 * cosine6;
        case 9:
            return v > 0.04 + 0.04 * nrSinRadians(u * 13.0) &&
                   v < 0.94 + 0.035 * nrCosRadians(u * 15.0);
        default: return 0;
    }
}

static uint32_t nrClampIndex(double value, uint32_t limit) {
    if (value <= 0.0) return 0u;
    if (value >= (double)limit) return limit - 1u;
    return (uint32_t)value;
}

static uint32_t nrMixRgb(uint32_t a, uint32_t b, double amount) {
    double inverse;
    uint32_t ar, ag, ab, br, bg, bb, r, g, blue;
    if (amount < 0.0) amount = 0.0;
    if (amount > 1.0) amount = 1.0;
    inverse = 1.0 - amount;
    ar = (a >> 16) & 255u; ag = (a >> 8) & 255u; ab = a & 255u;
    br = (b >> 16) & 255u; bg = (b >> 8) & 255u; bb = b & 255u;
    r = (uint32_t)(ar * inverse + br * amount + 0.5);
    g = (uint32_t)(ag * inverse + bg * amount + 0.5);
    blue = (uint32_t)(ab * inverse + bb * amount + 0.5);
    return (r << 16) | (g << 8) | blue;
}

static uint32_t nrFlattened(const uint32_t *cells, size_t offset) {
    uint32_t glyph = cells[offset];
    if (glyph == 0x2580u || glyph == 0x2584u || glyph == 0x258cu || glyph == 0x2590u)
        return nrMixRgb(cells[offset + 1], cells[offset + 2], 0.5);
    return cells[offset + 2];
}

static int nrArrayCellsValid(uint32_t width, uint32_t height, size_t bytesPerCell) {
    size_t cells;
    if (width == 0 || height == 0) return 0;
    if ((size_t)width > SIZE_MAX / (size_t)height) return 0;
    cells = (size_t)width * (size_t)height;
    return bytesPerCell != 0u && cells <= SIZE_MAX / bytesPerCell;
}

typedef struct {
    double aa, bb, cc, z, u, v, opacity;
} NrWindowTextureSample;

/* Return one for an eligible sample, zero for uncovered, and -1 for unsafe math. */
static int nrWindowTextureSampleAt(const NrWindowTextureVertex vertices[3],
                                 double denominator, size_t x, size_t y,
                                 NrWindowTextureSample *sample) {
    double inverse;
    sample->aa = ((vertices[1].y - vertices[2].y) * ((double)x + 0.5 - vertices[2].x) +
                  (vertices[2].x - vertices[1].x) * ((double)y + 0.5 - vertices[2].y)) / denominator;
    sample->bb = ((vertices[2].y - vertices[0].y) * ((double)x + 0.5 - vertices[2].x) +
                  (vertices[0].x - vertices[2].x) * ((double)y + 0.5 - vertices[2].y)) / denominator;
    sample->cc = 1.0 - sample->aa - sample->bb;
    if (!nrFinite(sample->aa) || !nrFinite(sample->bb) || !nrFinite(sample->cc)) return -1;
    if (sample->aa < -0.0001 || sample->bb < -0.0001 || sample->cc < -0.0001) return 0;
    inverse = sample->aa / vertices[0].z + sample->bb / vertices[1].z + sample->cc / vertices[2].z;
    if (!nrFinite(inverse) || inverse == 0.0) return -1;
    sample->z = 1.0 / inverse;
    sample->u = (sample->aa * vertices[0].u / vertices[0].z +
                 sample->bb * vertices[1].u / vertices[1].z +
                 sample->cc * vertices[2].u / vertices[2].z) / inverse;
    sample->v = (sample->aa * vertices[0].v / vertices[0].z +
                 sample->bb * vertices[1].v / vertices[1].z +
                 sample->cc * vertices[2].v / vertices[2].z) / inverse;
    sample->opacity = sample->aa * vertices[0].opacity +
                      sample->bb * vertices[1].opacity +
                      sample->cc * vertices[2].opacity;
    if (!nrFinite(sample->z) || !nrFinite(sample->u) || !nrFinite(sample->v) ||
        !nrFinite(sample->opacity)) return -1;
    return 1;
}

int nrWindowTextureTriangle(const NrWindowTextureVertex vertices[3],
                            uint32_t shape, uint32_t iris, double visibility,
                            uint32_t hitId, uint32_t textureWidth,
                            uint32_t textureHeight, const uint32_t *textureCells4,
                            uint32_t surfaceWidth, uint32_t surfaceHeight,
                            uint32_t clipX0, uint32_t clipY0,
                            uint32_t clipX1, uint32_t clipY1,
                            uint32_t *surfaceCells4, double *depth) {
    double denominator, minX, minY, maxX, maxY;
    size_t x0, x1, y0, y1, x, y;
    uint32_t i;
    if (!vertices || !textureCells4 || !surfaceCells4 || !depth ||
        !nrShapeValid(shape) || iris > 1u || !nrFinite(visibility) ||
        visibility < 0.0 || visibility > 1.0 ||
        !nrArrayCellsValid(textureWidth, textureHeight, 4u * sizeof(uint32_t)) ||
        !nrArrayCellsValid(surfaceWidth, surfaceHeight, 4u * sizeof(uint32_t)) ||
        !nrArrayCellsValid(surfaceWidth, surfaceHeight, sizeof(double)) ||
        clipX0 > clipX1 || clipY0 > clipY1 || clipX1 > surfaceWidth ||
        clipY1 > surfaceHeight) return -1;
    for (i = 0; i < 3u; ++i) {
        if (!nrFinite(vertices[i].x) || !nrFinite(vertices[i].y) ||
            !nrFinite(vertices[i].z) || !nrFinite(vertices[i].u) ||
            !nrFinite(vertices[i].v) || !nrFinite(vertices[i].opacity) ||
            vertices[i].z <= 0.0) return -1;
    }
    denominator = (vertices[1].y - vertices[2].y) *
                      (vertices[0].x - vertices[2].x) +
                  (vertices[2].x - vertices[1].x) *
                      (vertices[0].y - vertices[2].y);
    if (!nrFinite(denominator)) return -1;
    if (nrAbsValue(denominator) < 1e-8) return 0;
    minX = vertices[0].x;
    maxX = vertices[0].x;
    minY = vertices[0].y;
    maxY = vertices[0].y;
    for (i = 1; i < 3u; ++i) {
        if (vertices[i].x < minX) minX = vertices[i].x;
        if (vertices[i].x > maxX) maxX = vertices[i].x;
        if (vertices[i].y < minY) minY = vertices[i].y;
        if (vertices[i].y > maxY) maxY = vertices[i].y;
    }
    /* The source iterates floor(min) through ceil(max), inclusively. A raw
       bound can lie outside the clip while its rounded candidate cell still
       intersects it (for example minY=11.2 includes row 11). */
    if (clipX0 == clipX1 || clipY0 == clipY1 ||
        maxX <= (double)clipX0 - 1.0 || minX >= (double)clipX1 ||
        maxY <= (double)clipY0 - 1.0 || minY >= (double)clipY1) return 0;
    x0 = minX <= (double)clipX0 ? clipX0 : (size_t)nrFloorValue(minX);
    y0 = minY <= (double)clipY0 ? clipY0 : (size_t)nrFloorValue(minY);
    x1 = maxX >= (double)(clipX1 - 1u) ? (size_t)(clipX1 - 1u) : (size_t)maxX + (maxX != (double)(size_t)maxX);
    y1 = maxY >= (double)(clipY1 - 1u) ? (size_t)(clipY1 - 1u) : (size_t)maxY + (maxY != (double)(size_t)maxY);
    if (x0 < clipX0) x0 = clipX0;
    if (y0 < clipY0) y0 = clipY0;
    if (x1 >= clipX1) x1 = clipX1 - 1u;
    if (y1 >= clipY1) y1 = clipY1 - 1u;
    if (x0 > x1 || y0 > y1) return 0;

    /* Preflight all covered samples first, so unsafe float arithmetic cannot
       leave a partially rendered surface or depth buffer. */
    for (y = y0; y <= y1; ++y) {
        for (x = x0; x <= x1; ++x) {
            NrWindowTextureSample sample;
            if (nrWindowTextureSampleAt(vertices, denominator, x, y, &sample) < 0) return -1;
        }
    }

    for (y = y0; y <= y1; ++y) {
        for (x = x0; x <= x1; ++x) {
            NrWindowTextureSample sample;
            double irisDx, irisDy, opacity;
            size_t dest, src, offset;
            uint32_t glyph, oldForeground, background, sampledGlyph, sampledFg, sampledBg;
            if (nrWindowTextureSampleAt(vertices, denominator, x, y, &sample) <= 0) continue;
            if (!nrWindowTextureShapeContains(shape, sample.u, sample.v)) continue;
            if (iris) {
                irisDx = (sample.u - 0.5) * 2.0;
                irisDy = (sample.v - 0.5) * 2.0;
                if (nrSqrtValue(irisDx * irisDx + irisDy * irisDy) > visibility * 1.4142135623730950488)
                    continue;
            }
            dest = y * (size_t)surfaceWidth + x;
            if (sample.z > depth[dest] + 0.001) continue;
            src = ((size_t)nrClampIndex(nrFloorValue(sample.v * textureHeight), textureHeight) * textureWidth +
                   nrClampIndex(nrFloorValue(sample.u * textureWidth), textureWidth)) * 4u;
            offset = dest * 4u;
            opacity = sample.opacity;
            if (opacity < 0.0) opacity = 0.0;
            if (opacity > 1.0) opacity = 1.0;
            if (opacity < 0.005) continue;
            glyph = surfaceCells4[offset];
            oldForeground = surfaceCells4[offset + 1];
            background = nrFlattened(surfaceCells4, offset);
            sampledGlyph = textureCells4[src];
            sampledFg = textureCells4[src + 1];
            sampledBg = textureCells4[src + 2];
            surfaceCells4[offset + 2] = nrMixRgb(background, sampledBg, opacity);
            surfaceCells4[offset] = sampledGlyph;
            surfaceCells4[offset + 1] = nrMixRgb(surfaceCells4[offset + 2], sampledFg,
                                                 opacity * 1.2 > 1.0 ? 1.0 : opacity * 1.2);
            surfaceCells4[offset + 3] = hitId;
            depth[dest] = sample.z;
            if (sampledGlyph == 32u && opacity < 0.995 && glyph > 32u) {
                surfaceCells4[offset] = glyph;
                surfaceCells4[offset + 1] = nrMixRgb(surfaceCells4[offset + 2], oldForeground, 1.0 - opacity);
            }
            if (shape != 0u && shape != 1u &&
                (!nrWindowTextureShapeContains(shape, sample.u - 1.0 / textureWidth, sample.v) ||
                 !nrWindowTextureShapeContains(shape, sample.u + 1.0 / textureWidth, sample.v) ||
                 !nrWindowTextureShapeContains(shape, sample.u, sample.v - 1.0 / textureHeight) ||
                 !nrWindowTextureShapeContains(shape, sample.u, sample.v + 1.0 / textureHeight))) {
                surfaceCells4[offset] = 0x2219u;
                surfaceCells4[offset + 1] = nrMixRgb(surfaceCells4[offset + 2], sampledFg,
                    opacity * 1.6 > 1.0 ? 1.0 : opacity * 1.6);
            }
        }
    }
    return 0;
}
