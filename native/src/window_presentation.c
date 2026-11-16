#include "internal.h"
#include "window_presentation.h"

#include <limits.h>

static int has_field(const Json *json, const char *name) {
    return nrField(json, 0, name) >= 0;
}

static int number_field(const Json *json, const char *name, double *out,
                        double minimum, double maximum, int integer) {
    int token = nrField(json, 0, name);
    if (token < 0) return 1;
    double value;
    if (!nrNumber(json, token, &value) || value < minimum || value > maximum ||
        (integer && value != (int64_t)value)) return 0;
    *out = value;
    return 1;
}

static int action_from_name(const char *name) {
    if (!strcmp(name, "close")) return NR_WINDOW_SOURCE_ACTION_CLOSE;
    if (!strcmp(name, "minimize")) return NR_WINDOW_SOURCE_ACTION_MINIMIZE;
    if (!strcmp(name, "maximize")) return NR_WINDOW_SOURCE_ACTION_MAXIMIZE;
    if (!strcmp(name, "background")) return NR_WINDOW_SOURCE_ACTION_BACKGROUND;
    return -1;
}

static int parse_order(const Json *json, int token, int out[4]) {
    char text[128];
    if (nrString(json, token, text, sizeof(text)) < 0) return 0;
    int count = 0;
    char *start = text;
    for (char *at = text;; ++at) {
        if (*at != ',' && *at != '\0') continue;
        char delimiter = *at;
        *at = '\0';
        if (count >= 4 || !*start) return 0;
        int action = action_from_name(start);
        if (action < 0) return 0;
        out[count++] = action;
        if (!delimiter) break;
        start = at + 1;
    }
    return count == 4;
}

static int parse_glyphs(const Json *json, int token, uint32_t out[4]) {
    uint32_t decoded[32];
    int count = nrDecode(json, token, decoded, (int)(sizeof(decoded) / sizeof(decoded[0])));
    if (count < 0) return 0;
    int item = 0, scalarCount = 0;
    for (int i = 0; i <= count; ++i) {
        if (i < count && decoded[i] != ',') {
            if (item >= 4) return 0;
            out[item] = decoded[i];
            scalarCount++;
            continue;
        }
        if (item >= 4 || scalarCount != 1) return 0;
        item++;
        scalarCount = 0;
    }
    return item == 4;
}

static int parse_string_enum(const Json *json, const char *name,
                             const char *const *names, int count, int *out) {
    int token = nrField(json, 0, name);
    if (token < 0) return 1;
    for (int i = 0; i < count; ++i) {
        if (nrEqual(json, token, names[i])) {
            *out = i;
            return 1;
        }
    }
    return 0;
}

static int parse_source_fields(const Json *json,
                               NrWindowSourcePresentationOptions *options) {
    static const char *const chromeNames[] = {"mac", "windows", "gnome", "custom"};
    static const char *const sideNames[] = {"left", "right"};
    double number;
    if (!number_field(json, "depthFade", &options->depthFade, 0, .08, 0) ||
        !number_field(json, "controlWidth", &number, 5, 15, 1)) return 0;
    if (has_field(json, "controlWidth")) options->controlWidth = (int)number;
    if (!number_field(json, "controlHeight", &number, 3, 6, 1)) return 0;
    if (has_field(json, "controlHeight")) options->controlHeight = (int)number;
    if (!parse_string_enum(json, "chrome", chromeNames, 4, &options->chrome) ||
        !parse_string_enum(json, "customSide", sideNames, 2, &options->customSide)) return 0;

    int order = nrField(json, 0, "customOrder");
    if (order >= 0 && !parse_order(json, order, options->customOrder)) return 0;
    int glyphs = nrField(json, 0, "customGlyphs");
    if (glyphs >= 0 && !parse_glyphs(json, glyphs, options->customGlyphs)) return 0;
    return nrWindowSourcePresentationValid(options);
}

static int source_fields_present(const Json *json) {
    return has_field(json, "depthFade") || has_field(json, "chrome") ||
           has_field(json, "controlWidth") || has_field(json, "controlHeight") ||
           has_field(json, "customSide") || has_field(json, "customOrder") ||
           has_field(json, "customGlyphs");
}

int nrWindowPresentationPatch(const Json *json,
    const WindowSourcePresentationState *current, double canonicalAlpha,
    WindowSourcePresentationState *out, double *outAlpha) {
    if (!json || !current || !out || !outAlpha || json->count < 1 ||
        json->tokens[0].type != J_OBJECT || canonicalAlpha != canonicalAlpha ||
        canonicalAlpha < 0 || canonicalAlpha > 1 || current->enabled > 1 || current->reserved)
        return -1;

    int marker = nrField(json, 0, "sourcePresentation");
    int explicitMode = marker >= 0;
    int requested = 0;
    if (explicitMode && !nrBoolean(json, marker, &requested)) return -1;
    int sourceFields = source_fields_present(json);
    int alphaPresent = has_field(json, "alpha");
    if (explicitMode && !requested && sourceFields) return -1;
    if (!explicitMode && !sourceFields && !(current->enabled && alphaPresent)) return 0;

    WindowSourcePresentationState candidate;
    memset(&candidate, 0, sizeof(candidate));
    double alpha = canonicalAlpha;
    if (explicitMode && !requested) {
        *out = candidate;
        *outAlpha = canonicalAlpha;
        return 1;
    }

    if (current->enabled) {
        if (!nrWindowSourcePresentationValid(&current->options)) return -1;
        candidate = *current;
    } else {
        nrWindowSourcePresentationDefaults(&candidate.options);
        candidate.enabled = 1;
        if (!alphaPresent) alpha = .85;
    }
    candidate.enabled = 1;
    candidate.reserved = 0;
    candidate.options.opacity = alpha;
    if (!parse_source_fields(json, &candidate.options)) return -1;
    candidate.options.opacity = alpha;
    if (!nrWindowSourcePresentationValid(&candidate.options)) return -1;

    *out = candidate;
    *outAlpha = alpha;
    return 1;
}

int nrWindowPresentationControlRects(int frameWidth,
    const NrWindowSourcePresentationOptions *options,
    NrWindowPresentationControlRect out[4]) {
    if (frameWidth < 1 || !out || !nrWindowSourcePresentationValid(options)) return -1;
    NrWindowSourceControl controls[4];
    if (nrWindowSourcePresentationControls(options, controls)) return -1;
    int total = 0;
    for (int i = 0; i < 4; ++i) total += controls[i].width + 1;
    int start = controls[0].side == NR_WINDOW_SOURCE_SIDE_LEFT
              ? 3 : frameWidth - total - 3;
    if (start < 3) start = 3;
    NrWindowPresentationControlRect result[4];
    for (int i = 0; i < 4; ++i) {
        result[i].x = start + i * (controls[i].width + 1);
        result[i].y = 6;
        result[i].width = controls[i].width;
        result[i].height = controls[i].height;
        result[i].action = controls[i].action;
        result[i].index = controls[i].index;
    }
    for (int i = 0; i < 4; ++i) out[i] = result[i];
    return 0;
}

int nrWindowPresentationControlHit(int frameWidth,
    const NrWindowSourcePresentationOptions *options, int x, int y) {
    NrWindowPresentationControlRect rects[4];
    if (nrWindowPresentationControlRects(frameWidth, options, rects)) return -1;
    for (int i = 0; i < 4; ++i) {
        const NrWindowPresentationControlRect *rect = &rects[i];
        int64_t right = (int64_t)rect->x + rect->width;
        int64_t bottom = (int64_t)rect->y + rect->height;
        if (x >= rect->x && (int64_t)x < right && y >= rect->y && (int64_t)y < bottom)
            return rect->action;
    }
    return -1;
}

int nrValidWindowPresentation(const State *state) {
    if (!state) return 0;
    for (int i = 0; i < (int)NR_MAX_WINDOWS; ++i) {
        const WindowSourcePresentationState *record = &state->windowPresentation[i];
        if (record->enabled > 1 || record->reserved) return 0;
        if (!record->enabled) {
            const unsigned char *bytes = (const unsigned char *)record;
            for (size_t k = 0; k < sizeof(*record); ++k) if (bytes[k]) return 0;
            continue;
        }
        if (state->schema < NR_STATE_SCHEMA_WINDOW_PRESENTATION ||
            !state->windows[i].used ||
            !nrWindowSourcePresentationValid(&record->options) ||
            record->options.opacity != state->windows[i].alpha) return 0;
    }
    return 1;
}
