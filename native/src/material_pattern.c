#include "internal.h"
#include <string.h>

static int patternReject(NrContext *c, const char *message) {
    size_t n = strlen(message);
    if (n > sizeof(c->error) - 1) n = sizeof(c->error) - 1;
    memcpy(c->error, message, n);
    c->error[n] = 0;
    return -1;
}

static int enumValue(const Json *j, int object, const char *key,
                     const char *choices, uint32_t *value) {
    int token = nrField(j, object, key);
    if (token < 0) return 1;
    const char *at = choices;
    uint32_t index = 0;
    char candidate[48];
    while (*at) {
        size_t length = 0;
        while (at[length] && at[length] != ' ') length++;
        if (length >= sizeof(candidate)) return 0;
        memcpy(candidate, at, length);
        candidate[length] = 0;
        if (nrEqual(j, token, candidate)) {
            *value = index;
            return 1;
        }
        at += length;
        while (*at == ' ') at++;
        index++;
    }
    return 0;
}

static int numberValue(const Json *j, int object, const char *key,
                       int64_t minimum, uint64_t maximum, int isSigned,
                       int64_t *signedOut, uint64_t *unsignedOut) {
    int token = nrField(j, object, key);
    if (token < 0) return 1;
    double value;
    if (!nrNumber(j, token, &value)) return 0;
    if (isSigned) {
        if (value < (double)minimum || value > (double)(int64_t)maximum || value != (int64_t)value) return 0;
        *signedOut = (int64_t)value;
    } else {
        if (value < 0 || value > (double)maximum || value != (uint64_t)value) return 0;
        *unsignedOut = (uint64_t)value;
    }
    return 1;
}

#define SIGNED_FIELD(name, lo, hi) do { \
    int64_t signedValue = 0; uint64_t ignored = 0; \
    if (!numberValue(j, object, #name, lo, (uint64_t)(int64_t)(hi), 1, &signedValue, &ignored)) return 0; \
    if (nrField(j, object, #name) >= 0) c->name = (int32_t)signedValue; \
} while (0)
#define UNSIGNED_FIELD(name, lo, hi) do { \
    int64_t ignoredSigned = 0; uint64_t unsignedValue = 0; \
    if (!numberValue(j, object, #name, lo, hi, 0, &ignoredSigned, &unsignedValue)) return 0; \
    if (nrField(j, object, #name) >= 0) c->name = (uint32_t)unsignedValue; \
} while (0)

static int applySampler(const Json *j, int object, NrSourceMaterialSampler *c) {
    if (!nrAllowed(j, object,
        "kind focusMode focusXQ8 focusYQ8 periodMs saturationMilli brightnessMilli "
        "speedFalloffMilli saturationFalloffMilli brightnessFalloffMilli cellAspectMilli "
        "scaleQ8 angleMilliDegrees pivotXQ8 pivotYQ8 rotationPeriodMs rotationMode "
        "swingMilliDegrees phase1024 seed baseRgb inkRgb palette gradientWrap interpolation "
        "colorMode hueOffsetDegrees motion originXCells originYCells waveAmplitudeMilli reverse")) return 0;

    if (!enumValue(j, object, "kind", "solid linear diagonal wave rotating-linear plasma concentric moire aurora interference chevrons diamond", &c->pattern) ||
        !enumValue(j, object, "focusMode", "none row column radial diagonal-band", &c->focusMode) ||
        !enumValue(j, object, "rotationMode", "fixed continuous pendulum", &c->rotationMode) ||
        !enumValue(j, object, "gradientWrap", "loop mirror hard-stops", &c->gradientWrap) ||
        !enumValue(j, object, "interpolation", "linear eased", &c->interpolation) ||
        !enumValue(j, object, "colorMode", "palette hsv rgb-sine", &c->colorMode)) return 0;

    SIGNED_FIELD(focusXQ8, -1048576, 1048576);
    SIGNED_FIELD(focusYQ8, -1048576, 1048576);
    UNSIGNED_FIELD(periodMs, 50, 3600000);
    SIGNED_FIELD(saturationMilli, 0, 2000);
    SIGNED_FIELD(brightnessMilli, 0, 1000);
    UNSIGNED_FIELD(speedFalloffMilli, 10, 1000);
    UNSIGNED_FIELD(saturationFalloffMilli, 0, 1000);
    UNSIGNED_FIELD(brightnessFalloffMilli, 0, 1000);
    UNSIGNED_FIELD(cellAspectMilli, 500, 4000);
    UNSIGNED_FIELD(scaleQ8, 64, 262144);
    SIGNED_FIELD(angleMilliDegrees, -360000, 360000);
    SIGNED_FIELD(pivotXQ8, -1048576, 1048576);
    SIGNED_FIELD(pivotYQ8, -1048576, 1048576);
    UNSIGNED_FIELD(rotationPeriodMs, 100, 3600000);
    SIGNED_FIELD(swingMilliDegrees, 0, 360000);
    SIGNED_FIELD(phase1024, -65536, 65536);
    UNSIGNED_FIELD(seed, 0, 2147483647u);
    UNSIGNED_FIELD(baseRgb, 0, 0xffffffu);
    UNSIGNED_FIELD(inkRgb, 0, 0xffffffu);
    SIGNED_FIELD(hueOffsetDegrees, -3600, 3600);
    SIGNED_FIELD(originXCells, -4096, 4096);
    SIGNED_FIELD(originYCells, -4096, 4096);
    UNSIGNED_FIELD(waveAmplitudeMilli, 0, 4000);

    int motion = (int)c->motion, reverse = (int)c->reverse;
    int token = nrField(j, object, "motion");
    if (token >= 0 && !nrBoolean(j, token, &motion)) return 0;
    token = nrField(j, object, "reverse");
    if (token >= 0 && !nrBoolean(j, token, &reverse)) return 0;
    c->motion = (uint32_t)motion;
    c->reverse = (uint32_t)reverse;

    token = nrField(j, object, "palette");
    if (token >= 0) {
        if (j->tokens[token].type != J_ARRAY || j->tokens[token].count < 1 || j->tokens[token].count > 32) return 0;
        c->paletteCount = (uint32_t)j->tokens[token].count;
        int item = token + 1;
        for (uint32_t i = 0; i < c->paletteCount; ++i) {
            double value;
            if (!nrNumber(j, item, &value) || value < 0 || value > 0xffffff || value != (uint32_t)value) return 0;
            c->palette[i] = (uint32_t)value;
            item = j->tokens[item].next;
        }
        NrSourceMaterialSampler defaults;
        nrSourceMaterialSamplerDefaults(&defaults);
        for (uint32_t i = c->paletteCount; i < 32; ++i) c->palette[i] = defaults.palette[i];
    }
    return nrSourceMaterialSamplerValidate(c);
}

int nrMaterialPatternCommand(NrContext *context, State *state, const Json *json, int materialSlot) {
    if (!context || !state || !json || materialSlot < 0 || materialSlot >= NR_MATERIALS)
        return context ? patternReject(context, "Invalid material pattern target") : -1;
    int token = nrField(json, 0, "pattern");
    if (token < 0) return 0;
    if (state->schema < NR_STATE_SCHEMA_MATERIAL_PATTERN)
        return patternReject(context, "Material patterns require schema67");
    MaterialPattern *record = &state->materialPatterns[materialSlot];
    if (json->tokens[token].type == J_NULL) {
        memset(record, 0, sizeof(*record));
        return 0;
    }
    if (json->tokens[token].type != J_OBJECT)
        return patternReject(context, "Material pattern must be an object or null");
    NrSourceMaterialSampler candidate;
    if (record->used) candidate = record->sampler;
    else nrSourceMaterialSamplerDefaults(&candidate);
    if (!applySampler(json, token, &candidate))
        return patternReject(context, "Invalid material pattern control");
    record->used = 1;
    record->reserved = 0;
    record->sampler = candidate;
    return 0;
}

int nrValidMaterialPatterns(const State *state) {
    if (!state) return 0;
    for (int i = 0; i < NR_MATERIALS; ++i) {
        const MaterialPattern *record = &state->materialPatterns[i];
        if (record->used > 1 || record->reserved) return 0;
        if (!record->used) {
            const uint8_t *bytes = (const uint8_t *)&record->sampler;
            for (size_t k = 0; k < sizeof(record->sampler); ++k) if (bytes[k]) return 0;
        } else {
            if (state->schema < NR_STATE_SCHEMA_MATERIAL_PATTERN || !state->materials[i].used) return 0;
            if (!nrSourceMaterialSamplerValidate(&record->sampler)) return 0;
            NrSourceMaterialSampler defaults;
            nrSourceMaterialSamplerDefaults(&defaults);
            for (uint32_t k = record->sampler.paletteCount; k < 32; ++k)
                if (record->sampler.palette[k] != defaults.palette[k]) return 0;
        }
    }
    return 1;
}

uint32_t nrPaintAt(const State *state, int materialId, uint64_t timeUs,
                   int32_t xQ8, int32_t yQ8, double index, double *alpha) {
    uint32_t legacy = nrPaint(state, materialId, timeUs, index, alpha);
    if (!state || materialId < 0 || materialId >= NR_MATERIALS ||
        !state->materialPatterns[materialId].used) return legacy;
    uint32_t sampled = legacy;
    if (nrSourceMaterialSampleColor(&state->materialPatterns[materialId].sampler,
                                    timeUs, xQ8, yQ8, &sampled) < 0) return legacy;
    return sampled;
}
