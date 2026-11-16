#include "source_material_sampler.h"

/* The native core's pinned Q30 table shares the original 1024-step phases. */
#include "tables.inc"

#include <limits.h>
#include <stddef.h>
#include <string.h>

static int32_t modPhase(int64_t value, int32_t divisor) {
    int64_t r = value % divisor;
    return (int32_t)(r < 0 ? r + divisor : r);
}

static uint64_t abs64(int64_t value) {
    return value < 0 ? (uint64_t)(-(value + 1)) + 1 : (uint64_t)value;
}

static int32_t clamp32(int32_t value, int32_t lo, int32_t hi) {
    return value < lo ? lo : value > hi ? hi : value;
}

static int32_t sinPhase(int64_t phase) {
    int32_t index = modPhase(phase, 1024) * 4;
    int64_t scaled = (int64_t)SIN_Q30[index] * 1000;
    const int64_t half = (int64_t)1 << 29;
    const int64_t denominator = (int64_t)1 << 30;
    return (int32_t)(scaled >= 0 ? (scaled + half) / denominator : (scaled - half) / denominator);
}

static uint64_t sqrtInteger(uint64_t n) {
    uint64_t result = 0;
    uint64_t bit = UINT64_C(1) << 62;
    while (bit > n) bit >>= 2;
    while (bit) {
        if (n >= result + bit) {
            n -= result + bit;
            result = (result >> 1) + bit;
        } else {
            result >>= 1;
        }
        bit >>= 2;
    }
    return result;
}

static uint64_t squareSat(int64_t value) {
    uint64_t magnitude = abs64(value);
    if (magnitude > UINT32_MAX) return UINT64_MAX;
    return magnitude * magnitude;
}

static uint64_t distanceQ8(int64_t x, int64_t y) {
    uint64_t xx = squareSat(x), yy = squareSat(y);
    if (xx > UINT64_MAX - yy) return UINT32_MAX;
    return sqrtInteger(xx + yy);
}

static uint32_t rgb(int32_t r, int32_t g, int32_t b) {
    return (uint32_t)clamp32(r, 0, 255) << 16 |
           (uint32_t)clamp32(g, 0, 255) << 8 |
           (uint32_t)clamp32(b, 0, 255);
}

static int32_t red(uint32_t c) { return (int32_t)((c >> 16) & 255); }
static int32_t green(uint32_t c) { return (int32_t)((c >> 8) & 255); }
static int32_t blue(uint32_t c) { return (int32_t)(c & 255); }

static uint32_t mixRgb(uint32_t a, uint32_t b, int32_t p) {
    p = clamp32(p, 0, 1000);
    return rgb(red(a) + (red(b) - red(a)) * p / 1000,
               green(a) + (green(b) - green(a)) * p / 1000,
               blue(a) + (blue(b) - blue(a)) * p / 1000);
}

static int32_t smooth(int32_t p) {
    p = clamp32(p, 0, 1000);
    return (int32_t)(((int64_t)p * p * (3000 - 2 * p)) / 1000000);
}

static uint32_t saturate(uint32_t c, int32_t amount) {
    int32_t l = (2126 * red(c) + 7152 * green(c) + 722 * blue(c)) / 10000;
    return rgb(l + (red(c) - l) * amount / 1000,
               l + (green(c) - l) * amount / 1000,
               l + (blue(c) - l) * amount / 1000);
}

static uint32_t hsv(int64_t hue, int32_t saturation, int32_t value) {
    int32_t h = modPhase(hue, 360);
    int32_t c = value * saturation / 1000;
    int32_t within = h % 120;
    int32_t x = c * (60 - (within > 60 ? within - 60 : 60 - within)) / 60;
    int32_t m = value - c;
    int32_t r = 0, g = 0, b = 0;
    switch (h / 60) {
        case 0: r = c; g = x; break;
        case 1: r = x; g = c; break;
        case 2: g = c; b = x; break;
        case 3: g = x; b = c; break;
        case 4: r = x; b = c; break;
        default: r = c; b = x; break;
    }
    return rgb((r + m) * 255 / 1000, (g + m) * 255 / 1000, (b + m) * 255 / 1000);
}

static int32_t decay(int32_t value, uint32_t factor, uint32_t distance) {
    if (distance > 256) distance = 256;
    for (uint32_t i = 0; i < distance; ++i) value = value * (int32_t)factor / 1000;
    return value;
}

static uint32_t paletteColor(const NrSourceMaterialSampler *c, int64_t phase) {
    if (c->colorMode == NR_SOURCE_COLOR_HSV)
        return hsv(phase * 360 / 1024 + c->hueOffsetDegrees, 1000, 1000);
    if (c->colorMode == NR_SOURCE_COLOR_RGB_SINE)
        return rgb((sinPhase(phase) + 1000) * 255 / 2000,
                   (sinPhase(phase + 341) + 1000) * 255 / 2000,
                   (sinPhase(phase + 683) + 1000) * 255 / 2000);
    if (c->paletteCount == 1) return c->palette[0];
    int32_t p, index;
    if (c->gradientWrap == NR_SOURCE_GRADIENT_MIRROR) {
        p = modPhase(phase, 2048);
        if (p > 1024) p = 2048 - p;
        p *= (int32_t)c->paletteCount - 1;
        index = p / 1024;
        if (index >= (int32_t)c->paletteCount - 1) return c->palette[c->paletteCount - 1];
    } else {
        p = modPhase(phase, 1024) * (int32_t)c->paletteCount;
        index = p / 1024;
    }
    int32_t blend = (p % 1024) * 1000 / 1024;
    if (c->interpolation) blend = smooth(blend);
    if (c->gradientWrap == NR_SOURCE_GRADIENT_HARD_STOPS) blend = 0;
    return mixRgb(c->palette[index], c->palette[(index + 1) % c->paletteCount], blend);
}

int nrSourceMaterialPaletteColor(const NrSourceMaterialSampler *c, int64_t phase,
                                 uint32_t *outRgb) {
    if (!outRgb || !nrSourceMaterialSamplerValidate(c)) return -1;
    *outRgb = paletteColor(c, phase);
    return 0;
}

void nrSourceMaterialSamplerDefaults(NrSourceMaterialSampler *c) {
    static const uint32_t palette[] = {0x28304f, 0x785c89, 0x367876, 0xae7357, 0x504565};
    if (!c) return;
    memset(c, 0, sizeof(*c));
    c->pattern = NR_SOURCE_PATTERN_PLASMA;
    c->focusMode = NR_SOURCE_FOCUS_NONE;
    c->focusXQ8 = 12800;
    c->focusYQ8 = 4096;
    c->periodMs = 5000;
    c->saturationMilli = 700;
    c->brightnessMilli = 260;
    c->speedFalloffMilli = 500;
    c->saturationFalloffMilli = 760;
    c->brightnessFalloffMilli = 940;
    c->cellAspectMilli = 2000;
    c->scaleQ8 = 6144;
    c->pivotXQ8 = 12800;
    c->pivotYQ8 = 4096;
    c->rotationPeriodMs = 18000;
    c->rotationMode = NR_SOURCE_ROTATION_CONTINUOUS;
    c->swingMilliDegrees = 65000;
    c->seed = 7319;
    c->baseRgb = 0x11100e;
    c->inkRgb = 0xe2d9c9;
    c->paletteCount = 5;
    c->interpolation = 1;
    c->motion = 1;
    c->waveAmplitudeMilli = 640;
    for (uint32_t i = 0; i < 32; ++i) c->palette[i] = palette[i % 5];
}

int nrSourceMaterialSamplerValidate(const NrSourceMaterialSampler *c) {
    if (!c || c->pattern > NR_SOURCE_PATTERN_DIAMOND || c->focusMode > NR_SOURCE_FOCUS_DIAGONAL_BAND ||
        c->focusXQ8 < -1048576 || c->focusXQ8 > 1048576 || c->focusYQ8 < -1048576 || c->focusYQ8 > 1048576 ||
        c->periodMs < 50 || c->periodMs > 3600000 || c->saturationMilli < 0 || c->saturationMilli > 2000 ||
        c->brightnessMilli < 0 || c->brightnessMilli > 1000 || c->speedFalloffMilli < 10 || c->speedFalloffMilli > 1000 ||
        c->saturationFalloffMilli > 1000 || c->brightnessFalloffMilli > 1000 || c->cellAspectMilli < 500 || c->cellAspectMilli > 4000 ||
        c->scaleQ8 < 64 || c->scaleQ8 > 262144 || c->angleMilliDegrees < -360000 || c->angleMilliDegrees > 360000 ||
        c->pivotXQ8 < -1048576 || c->pivotXQ8 > 1048576 || c->pivotYQ8 < -1048576 || c->pivotYQ8 > 1048576 ||
        c->rotationPeriodMs < 100 || c->rotationPeriodMs > 3600000 || c->rotationMode > NR_SOURCE_ROTATION_PENDULUM ||
        c->swingMilliDegrees < 0 || c->swingMilliDegrees > 360000 || c->phase1024 < -65536 || c->phase1024 > 65536 ||
        c->seed > 2147483647u || c->baseRgb > 0xffffffu || c->inkRgb > 0xffffffu ||
        c->paletteCount < 1 || c->paletteCount > 32 || c->gradientWrap > NR_SOURCE_GRADIENT_HARD_STOPS ||
        c->interpolation > 1 || c->colorMode > NR_SOURCE_COLOR_RGB_SINE || c->hueOffsetDegrees < -3600 ||
        c->hueOffsetDegrees > 3600 || c->motion > 1 || c->originXCells < -4096 || c->originXCells > 4096 ||
        c->originYCells < -4096 || c->originYCells > 4096 || c->waveAmplitudeMilli > 4000 || c->reverse > 1) return 0;
    for (uint32_t i = 0; i < c->paletteCount; ++i) if (c->palette[i] > 0xffffffu) return 0;
    return 1;
}

int nrSourceMaterialSampleColor(const NrSourceMaterialSampler *c, uint64_t timeUs,
                                int32_t xQ8, int32_t yQ8, uint32_t *outRgb) {
    if (!outRgb || !nrSourceMaterialSamplerValidate(c)) return -1;

    uint64_t timeMs = c->motion ? timeUs / 1000 : 0;
    uint64_t period = c->periodMs;
    int64_t fx = (int64_t)xQ8 - c->focusXQ8, fy = (int64_t)yQ8 - c->focusYQ8;
    uint32_t distance = 0;
    if (c->focusMode == NR_SOURCE_FOCUS_ROW) distance = (uint32_t)(abs64(fy) / 256);
    if (c->focusMode == NR_SOURCE_FOCUS_COLUMN) distance = (uint32_t)(abs64(fx) / 256);
    if (c->focusMode == NR_SOURCE_FOCUS_RADIAL)
        distance = (uint32_t)(distanceQ8(fx, fy * c->cellAspectMilli / 1000) / 256);
    if (c->focusMode == NR_SOURCE_FOCUS_DIAGONAL_BAND) distance = (uint32_t)(abs64(fx - fy) / 362);
    for (uint32_t d = 0; d < distance && d < 64; ++d) {
        period = period * 1000 / c->speedFalloffMilli;
        if (period > 3600000000u) { period = 3600000000u; break; }
    }
    int32_t phase = (int32_t)((timeMs % period) * 1024 / period);
    if (c->reverse) phase = -phase;
    int32_t saturation = decay(c->saturationMilli, c->saturationFalloffMilli, (uint32_t)distance);
    int32_t brightness = decay(c->brightnessMilli, c->brightnessFalloffMilli, (uint32_t)distance);
    int64_t dx = (int64_t)xQ8 - c->pivotXQ8;
    int64_t dy = ((int64_t)yQ8 - c->pivotYQ8) * c->cellAspectMilli / 1000;
    int32_t angle = (int32_t)((int64_t)c->angleMilliDegrees * 1024 / 360000);
    int32_t rotation = (int32_t)((timeMs % c->rotationPeriodMs) * 1024 / c->rotationPeriodMs);
    if (c->reverse) rotation = -rotation;
    if (c->rotationMode == NR_SOURCE_ROTATION_CONTINUOUS) angle += rotation;
    if (c->rotationMode == NR_SOURCE_ROTATION_PENDULUM)
        angle += (int32_t)((int64_t)sinPhase(rotation) * c->swingMilliDegrees * 1024 / 360000000);
    int64_t px = ((int64_t)xQ8 + (int64_t)c->originXCells * 256) * 1024 / c->scaleQ8;
    int64_t py = ((int64_t)yQ8 + (int64_t)c->originYCells * 256) * c->cellAspectMilli * 1024 / (1000 * (int64_t)c->scaleQ8);
    int64_t p = 0;
    switch (c->pattern) {
        case NR_SOURCE_PATTERN_SOLID:
            *outRgb = c->baseRgb;
            return 0;
        case NR_SOURCE_PATTERN_LINEAR: p = px; break;
        case NR_SOURCE_PATTERN_DIAGONAL: p = (px + py) / 2; break;
        case NR_SOURCE_PATTERN_WAVE: p = px + (int64_t)sinPhase(py + phase) * c->waveAmplitudeMilli / 1000; break;
        case NR_SOURCE_PATTERN_ROTATING_LINEAR:
            p = (dx * sinPhase(angle + 256) + dy * sinPhase(angle)) * 1024 / (1000 * (int64_t)c->scaleQ8); break;
        case NR_SOURCE_PATTERN_PLASMA:
            p = (sinPhase(px + phase) + sinPhase(py - phase) + sinPhase((px + py) / 2 + phase) +
                 sinPhase((int64_t)distanceQ8(dx, dy) * 1024 / c->scaleQ8 - phase)) / 4; break;
        case NR_SOURCE_PATTERN_CONCENTRIC:
            p = (int64_t)distanceQ8(fx, fy * c->cellAspectMilli / 1000) * 1024 / c->scaleQ8; break;
        case NR_SOURCE_PATTERN_MOIRE: p = sinPhase(px + phase) + sinPhase(px * 103 / 100 + py / 2 - phase); break;
        case NR_SOURCE_PATTERN_AURORA:
            p = py / 2 + (int64_t)sinPhase(px / 2 + phase) * c->waveAmplitudeMilli / 1000 + sinPhase(px * 3 - phase) / 5; break;
        case NR_SOURCE_PATTERN_INTERFERENCE:
            p = (sinPhase(px + phase) + sinPhase(py - phase) + sinPhase(px - py + phase)) / 3; break;
        case NR_SOURCE_PATTERN_CHEVRONS: p = (modPhase(px, 2048) >= 1024 ? modPhase(px, 2048) - 1024 : 1024 - modPhase(px, 2048)) + py; break;
        case NR_SOURCE_PATTERN_DIAMOND:
            p = ((int64_t)abs64(fx) + (int64_t)abs64(fy * c->cellAspectMilli / 1000)) * 1024 / c->scaleQ8; break;
        default: return -1;
    }
    p += phase + c->phase1024;
    *outRgb = mixRgb(c->baseRgb, saturate(paletteColor(c, p), saturation), brightness);
    return 0;
}
