#include "window_palette_source.h"

#include <float.h>
#include <string.h>

extern double nrClamp(double, double, double);
extern double nrAbs(double);
extern double nrPowPositive(double, double);
extern double nrSqrt(double);

#include "window_palette_kernel.inc"

enum { NR_WINDOW_PALETTE_MAX_RGB = 0xffffffu };
static const double NR_WINDOW_PALETTE_MAX_SAFE = 9007199254740991.0;

typedef struct {
    double lightness;
    double chroma;
    double hue;
} NrOklchStop;

static int finiteNumber(double value) {
    return value == value && value <= DBL_MAX && value >= -DBL_MAX;
}

static double floorNumber(double value) {
    if (value >= 9007199254740992.0 || value <= -9007199254740992.0)
        return value;
    int64_t integer = (int64_t)value;
    return (double)(integer - (value < (double)integer));
}

static double positiveModulo(double value, double modulus) {
    double result = value - modulus * floorNumber(value / modulus);
    if (result < 0.0) result += modulus;
    if (result >= modulus) result = 0.0;
    return result;
}

static double channelLinear(uint32_t channel) {
    double value = channel / 255.0;
    return value <= .04045 ? value / 12.92 : nrPowPositive((value + .055) / 1.055, 2.4);
}

/* Deterministic high-precision atan2 conversion for the freestanding Wasm
 * build. The transformed alternating series remains below sqrt(2)-1. */
static double atanSmall(double value) {
    double reduced = value / (1.0 + nrSqrt(1.0 + value * value));
    double squared = reduced * reduced;
    double term = reduced, sum = reduced;
    for (int denominator = 3; denominator <= 81; denominator += 2) {
        term *= -squared;
        sum += term / denominator;
    }
    return 2.0 * sum;
}

static double atan2Degrees(double y, double x) {
    if (x == 0.0 && y == 0.0) return 0.0;
    double ax = nrAbs(x), ay = nrAbs(y), angle;
    if (ax >= ay) angle = atanSmall(ay / ax) * (180.0 / 3.14159265358979323846);
    else angle = 90.0 - atanSmall(ax / ay) * (180.0 / 3.14159265358979323846);
    if (x < 0.0) angle = 180.0 - angle;
    return y < 0.0 ? -angle : angle;
}

static NrOklchStop rgbToOklch(uint32_t rgb) {
    double r = channelLinear((rgb >> 16) & 255u);
    double g = channelLinear((rgb >> 8) & 255u);
    double b = channelLinear(rgb & 255u);
    double l = nrPowPositive(.4122214708 * r + .5363325363 * g + .0514459929 * b, 1.0 / 3.0);
    double m = nrPowPositive(.2119034982 * r + .6806995451 * g + .1073969566 * b, 1.0 / 3.0);
    double s = nrPowPositive(.0883024619 * r + .2817188376 * g + .6299787005 * b, 1.0 / 3.0);
    double a = 1.9779984951 * l - 2.428592205 * m + .4505937099 * s;
    double bb = .0259040371 * l + .7827717662 * m - .808675766 * s;
    NrOklchStop result;
    result.lightness = .2104542553 * l + .793617785 * m - .0040720468 * s;
    result.chroma = nrSqrt(a * a + bb * bb);
    result.hue = positiveModulo(atan2Degrees(bb, a), 360.0);
    return result;
}

static int inRange(double value, double minimum, double maximum) {
    return finiteNumber(value) && value >= minimum && value <= maximum;
}

void nrWindowPaletteSourceDefaults(NrWindowPaletteSourceConfig *config) {
    if (!config) return;
    memset(config, 0, sizeof(*config));
    static const uint32_t colors[5] = {
        0x647795u, 0xaf88bbu, 0x69a9a5u, 0xb89477u, 0x73709fu
    };
    config->colorCount = 5;
    memcpy(config->colors, colors, sizeof(colors));
    for (uint32_t i = 0; i < NR_WINDOW_PALETTE_SOURCE_MAX_STOPS; ++i)
        config->weights[i] = 1.0;
    config->backgroundRgb = 0x101319u;
    config->inkRgb = 0xdfd8ccu;
    config->lockLightness = 1;
    config->lightness = .62;
    config->chroma = .14;
    config->brightness = .28;
    config->hueOffsetDegrees = 0.0;
    config->feather = 1.0;
    config->textLightness = .83;
    config->textChroma = .10;
}

int nrWindowPaletteSourceValidate(const NrWindowPaletteSourceConfig *config) {
    if (!config || config->colorCount < 1u ||
        config->colorCount > NR_WINDOW_PALETTE_SOURCE_MAX_STOPS ||
        config->weightCount > NR_WINDOW_PALETTE_SOURCE_MAX_STOPS ||
        config->backgroundRgb > NR_WINDOW_PALETTE_MAX_RGB ||
        config->inkRgb > NR_WINDOW_PALETTE_MAX_RGB ||
        config->lockLightness > 1u || config->reserved != 0u ||
        !inRange(config->lightness, .05, .95) ||
        !inRange(config->chroma, 0.0, .4) ||
        !inRange(config->brightness, 0.0, 1.0) ||
        !inRange(config->hueOffsetDegrees, -360.0, 360.0) ||
        !inRange(config->feather, 0.0, 1.0) ||
        !inRange(config->textLightness, .35, .95) ||
        !inRange(config->textChroma, 0.0, .3)) return 0;
    for (uint32_t i = 0; i < config->colorCount; ++i)
        if (config->colors[i] > NR_WINDOW_PALETTE_MAX_RGB) return 0;
    for (uint32_t i = 0; i < config->weightCount; ++i)
        if (!inRange(config->weights[i], .05, 16.0)) return 0;
    return 1;
}

int nrWindowPaletteSourcePrepare(const NrWindowPaletteSourceConfig *config,
                                 NrWindowPaletteSourcePrepared *prepared) {
    if (!prepared || !nrWindowPaletteSourceValidate(config)) return -1;

    NrWindowPaletteSourcePrepared candidate;
    NrOklchStop stops[NR_WINDOW_PALETTE_SOURCE_MAX_STOPS];
    double weights[NR_WINDOW_PALETTE_SOURCE_MAX_STOPS];
    double cumulative[NR_WINDOW_PALETTE_SOURCE_MAX_STOPS + 1u];
    double stopTotal = 0.0;
    for (uint32_t i = 0; i < config->colorCount; ++i) {
        stops[i] = rgbToOklch(config->colors[i]);
        weights[i] = i < config->weightCount ? config->weights[i] : 1.0;
        cumulative[i] = stopTotal;
        stopTotal += weights[i];
    }
    cumulative[config->colorCount] = stopTotal;
    if (!finiteNumber(stopTotal) || stopTotal <= 0.0) return -1;

    double backgroundLightness = rgbToOklch(config->backgroundRgb).lightness;
    for (uint32_t i = 0; i < NR_WINDOW_PALETTE_SOURCE_RAMP_SIZE; ++i) {
        double position = ((double)i / NR_WINDOW_PALETTE_SOURCE_RAMP_SIZE) * stopTotal;
        uint32_t index = 0;
        while (index + 1u < config->colorCount && cumulative[index + 1u] <= position)
            ++index;
        NrOklchStop a = stops[index];
        NrOklchStop b = stops[(index + 1u) % config->colorCount];
        double fraction = (position - cumulative[index]) / weights[index];
        if (config->feather == 0.0) fraction = 0.0;
        else {
            double t = nrClamp((fraction - (1.0 - config->feather) / 2.0) /
                               config->feather, 0.0, 1.0);
            fraction = t * t * (3.0 - 2.0 * t);
        }
        double h1 = a.hue, h2 = b.hue;
        if (a.chroma < .005) h1 = h2;
        if (b.chroma < .005) h2 = h1;
        double delta = positiveModulo(h2 - h1 + 540.0, 360.0) - 180.0;
        double hue = h1 + delta * fraction + config->hueOffsetDegrees;
        double lightness = config->lockLightness ? config->lightness :
            a.lightness * (1.0 - fraction) + b.lightness * fraction;
        double chroma = a.chroma * (1.0 - fraction) + b.chroma * fraction + .025;
        chroma = chroma < config->chroma ? chroma : config->chroma;
        double mixedLightness = nrClamp(backgroundLightness +
            (lightness - backgroundLightness) * config->brightness, 0.0, 1.0);
        double mixedChroma = nrClamp(chroma * config->brightness, 0.0, .4);
        /* Keep the original engine's L/1000 and C/10000 integer units. */
        int64_t lightnessUnits = (int64_t)floorNumber(mixedLightness * 1000.0 + .5);
        int64_t chromaUnits = (int64_t)floorNumber(mixedChroma * 10000.0 + .5);
        candidate.ramp[i] = nrWindowPaletteSourceOklch((int32_t)lightnessUnits,
            (int32_t)chromaUnits, (int32_t)floorNumber(hue * 1000.0 + .5));
    }
    int64_t textLightnessUnits = (int64_t)floorNumber(config->textLightness * 1000.0 + .5);
    int64_t textChromaUnits = (int64_t)floorNumber(config->textChroma * 10000.0 + .5);
    for (uint32_t hue = 0; hue < NR_WINDOW_PALETTE_SOURCE_WHEEL_SIZE; ++hue)
        candidate.wheel[hue] = nrWindowPaletteSourceOklch((int32_t)textLightnessUnits,
            (int32_t)textChromaUnits, (int32_t)(hue * 1000u));
    candidate.stopTotal = stopTotal;
    memcpy(prepared, &candidate, sizeof(candidate));
    return 0;
}

int nrWindowPaletteSourceColorAt(const NrWindowPaletteSourcePrepared *prepared,
                                 double phase, uint32_t *rgb) {
    if (!prepared || !rgb || !finiteNumber(phase) ||
        !finiteNumber(prepared->stopTotal) || prepared->stopTotal <= 0.0 ||
        nrAbs(phase / prepared->stopTotal) > NR_WINDOW_PALETTE_MAX_SAFE) return -1;
    double fraction = phase / prepared->stopTotal;
    fraction -= floorNumber(fraction);
    uint32_t index = (uint32_t)floorNumber(fraction * NR_WINDOW_PALETTE_SOURCE_RAMP_SIZE);
    if (index >= NR_WINDOW_PALETTE_SOURCE_RAMP_SIZE)
        index = NR_WINDOW_PALETTE_SOURCE_RAMP_SIZE - 1u;
    *rgb = prepared->ramp[index];
    return 0;
}

int nrWindowPaletteSourceInk(const NrWindowPaletteSourcePrepared *prepared,
                             double hue, uint32_t *rgb) {
    if (!prepared || !rgb || !finiteNumber(hue) ||
        nrAbs(hue) > NR_WINDOW_PALETTE_MAX_SAFE) return -1;
    double rounded = hue >= 9007199254740992.0 || hue <= -9007199254740992.0 ?
        hue : floorNumber(hue + .5);
    int64_t indexValue = (int64_t)rounded % (int64_t)NR_WINDOW_PALETTE_SOURCE_WHEEL_SIZE;
    if (indexValue < 0) indexValue += NR_WINDOW_PALETTE_SOURCE_WHEEL_SIZE;
    uint32_t index = (uint32_t)indexValue;
    *rgb = prepared->wheel[index];
    return 0;
}

int nrWindowPaletteSourceTextInk(double lightness,double chroma,double hue,uint32_t *rgb) {
    if(!rgb||!finiteNumber(lightness)||lightness<0||lightness>1||!finiteNumber(chroma)||chroma<0||chroma>.4||!finiteNumber(hue)||hue< -9007199254740991.0||hue>9007199254740991.0)return -1;
    double rounded=floorNumber(hue+.5);rounded=positiveModulo(rounded,360);
    *rgb=nrWindowPaletteSourceOklch((int32_t)floorNumber(lightness*1000+.5),(int32_t)floorNumber(chroma*10000+.5),(int32_t)rounded*1000);return 0;
}

uint32_t nrWindowPaletteSourceFixedOklch(int32_t l,int32_t c,int32_t h){return nrWindowPaletteSourceOklch(l,c,h);}
