#ifndef NOCTURNE_SOURCE_MATERIAL_SAMPLER_H
#define NOCTURNE_SOURCE_MATERIAL_SAMPLER_H

#include <stdint.h>

typedef struct {
    uint32_t pattern;
    uint32_t focusMode;
    int32_t focusXQ8;
    int32_t focusYQ8;
    uint32_t periodMs;
    int32_t saturationMilli;
    int32_t brightnessMilli;
    uint32_t speedFalloffMilli;
    uint32_t saturationFalloffMilli;
    uint32_t brightnessFalloffMilli;
    uint32_t cellAspectMilli;
    uint32_t scaleQ8;
    int32_t angleMilliDegrees;
    int32_t pivotXQ8;
    int32_t pivotYQ8;
    uint32_t rotationPeriodMs;
    uint32_t rotationMode;
    int32_t swingMilliDegrees;
    int32_t phase1024;
    uint32_t seed;
    uint32_t baseRgb;
    uint32_t inkRgb;
    uint32_t paletteCount;
    uint32_t gradientWrap;
    uint32_t interpolation;
    uint32_t colorMode;
    int32_t hueOffsetDegrees;
    uint32_t motion;
    int32_t originXCells;
    int32_t originYCells;
    uint32_t waveAmplitudeMilli;
    uint32_t reverse;
    uint32_t palette[32];
} NrSourceMaterialSampler;

enum {
    NR_SOURCE_PATTERN_SOLID = 0,
    NR_SOURCE_PATTERN_LINEAR,
    NR_SOURCE_PATTERN_DIAGONAL,
    NR_SOURCE_PATTERN_WAVE,
    NR_SOURCE_PATTERN_ROTATING_LINEAR,
    NR_SOURCE_PATTERN_PLASMA,
    NR_SOURCE_PATTERN_CONCENTRIC,
    NR_SOURCE_PATTERN_MOIRE,
    NR_SOURCE_PATTERN_AURORA,
    NR_SOURCE_PATTERN_INTERFERENCE,
    NR_SOURCE_PATTERN_CHEVRONS,
    NR_SOURCE_PATTERN_DIAMOND
};

enum {
    NR_SOURCE_FOCUS_NONE = 0,
    NR_SOURCE_FOCUS_ROW,
    NR_SOURCE_FOCUS_COLUMN,
    NR_SOURCE_FOCUS_RADIAL,
    NR_SOURCE_FOCUS_DIAGONAL_BAND
};

enum {
    NR_SOURCE_ROTATION_FIXED = 0,
    NR_SOURCE_ROTATION_CONTINUOUS,
    NR_SOURCE_ROTATION_PENDULUM
};

enum {
    NR_SOURCE_GRADIENT_LOOP = 0,
    NR_SOURCE_GRADIENT_MIRROR,
    NR_SOURCE_GRADIENT_HARD_STOPS
};

enum {
    NR_SOURCE_COLOR_PALETTE = 0,
    NR_SOURCE_COLOR_HSV,
    NR_SOURCE_COLOR_RGB_SINE
};

void nrSourceMaterialSamplerDefaults(NrSourceMaterialSampler *config);
int nrSourceMaterialSamplerValidate(const NrSourceMaterialSampler *config);
/* Returns 0 on success, -1 on invalid arguments. Invalid calls preserve outRgb. */
int nrSourceMaterialSampleColor(const NrSourceMaterialSampler *config,
                                uint64_t timeUs, int32_t xQ8, int32_t yQ8,
                                uint32_t *outRgb);
/* Exact rc.2 stPalette phase lookup; failure preserves outRgb. */
int nrSourceMaterialPaletteColor(const NrSourceMaterialSampler *config,
                                 int64_t phase, uint32_t *outRgb);

#endif
