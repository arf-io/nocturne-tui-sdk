#include "window_source_presentation.h"

static int in_range(double value, double minimum, double maximum) {
    return value == value && value >= minimum && value <= maximum;
}

static int scalar_valid(uint32_t scalar) {
    if (scalar > 0x10ffffu || (scalar >= 0xd800u && scalar <= 0xdfffu)) return 0;
    if (scalar <= 0x1fu || (scalar >= 0x7fu && scalar <= 0x9fu)) return 0;
    return 1;
}

void nrWindowSourcePresentationDefaults(NrWindowSourcePresentationOptions *options) {
    if (!options) return;
    options->opacity = .85;
    options->depthFade = .008;
    options->chrome = NR_WINDOW_SOURCE_CHROME_MAC;
    options->controlWidth = 10;
    options->controlHeight = 3;
    options->customSide = NR_WINDOW_SOURCE_SIDE_RIGHT;
    options->customOrder[0] = NR_WINDOW_SOURCE_ACTION_MINIMIZE;
    options->customOrder[1] = NR_WINDOW_SOURCE_ACTION_MAXIMIZE;
    options->customOrder[2] = NR_WINDOW_SOURCE_ACTION_BACKGROUND;
    options->customOrder[3] = NR_WINDOW_SOURCE_ACTION_CLOSE;
    options->customGlyphs[0] = 0x2212u;
    options->customGlyphs[1] = 0x25a1u;
    options->customGlyphs[2] = 0x25c7u;
    options->customGlyphs[3] = 0x00d7u;
}

int nrWindowSourcePresentationValid(const NrWindowSourcePresentationOptions *options) {
    if (!options || !in_range(options->opacity, 0, 1) ||
        !in_range(options->depthFade, 0, .08) ||
        options->chrome < NR_WINDOW_SOURCE_CHROME_MAC ||
        options->chrome > NR_WINDOW_SOURCE_CHROME_CUSTOM ||
        options->controlWidth < 5 || options->controlWidth > 15 ||
        options->controlHeight < 3 || options->controlHeight > 6 ||
        options->customSide < NR_WINDOW_SOURCE_SIDE_LEFT ||
        options->customSide > NR_WINDOW_SOURCE_SIDE_RIGHT) return 0;

    unsigned seen = 0;
    for (int i = 0; i < 4; ++i) {
        int action = options->customOrder[i];
        if (action < NR_WINDOW_SOURCE_ACTION_CLOSE ||
            action > NR_WINDOW_SOURCE_ACTION_BACKGROUND) return 0;
        unsigned bit = 1u << (unsigned)action;
        if (seen & bit) return 0;
        seen |= bit;
        if (!scalar_valid(options->customGlyphs[i])) return 0;
    }
    return seen == 0x0fu;
}

int nrWindowSourcePresentationOpacity(
    const NrWindowSourcePresentationOptions *options,
    double worldZ, double *opacity) {
    if (!opacity || !nrWindowSourcePresentationValid(options) ||
        !in_range(worldZ, -1000, 1000)) return -1;
    double factor = 1;
    if (worldZ > 0) {
        factor = 1 - worldZ * options->depthFade;
        if (factor < .2) factor = .2;
    }
    *opacity = options->opacity * factor;
    return 0;
}

static uint32_t action_color(int action) {
    switch (action) {
    case NR_WINDOW_SOURCE_ACTION_CLOSE: return 0xf18c8cu;
    case NR_WINDOW_SOURCE_ACTION_MINIMIZE: return 0xd7be7au;
    case NR_WINDOW_SOURCE_ACTION_MAXIMIZE: return 0x8bcdb5u;
    default: return 0xb7a8e0u;
    }
}

static const char *action_label(int action) {
    switch (action) {
    case NR_WINDOW_SOURCE_ACTION_CLOSE: return "Close";
    case NR_WINDOW_SOURCE_ACTION_MINIMIZE: return "Min";
    case NR_WINDOW_SOURCE_ACTION_MAXIMIZE: return "Max";
    default: return "Back";
    }
}

static uint32_t profile_glyph(int chrome, int action) {
    if (chrome == NR_WINDOW_SOURCE_CHROME_MAC) {
        switch (action) {
        case NR_WINDOW_SOURCE_ACTION_CLOSE: return 0x25cfu;
        case NR_WINDOW_SOURCE_ACTION_MINIMIZE: return 0x2212u;
        case NR_WINDOW_SOURCE_ACTION_MAXIMIZE: return '+';
        default: return 0x25c7u;
        }
    }
    if (chrome == NR_WINDOW_SOURCE_CHROME_GNOME) {
        switch (action) {
        case NR_WINDOW_SOURCE_ACTION_CLOSE: return 0x00d7u;
        case NR_WINDOW_SOURCE_ACTION_MINIMIZE: return 0x2304u;
        case NR_WINDOW_SOURCE_ACTION_MAXIMIZE: return 0x25a1u;
        default: return 0x25b1u;
        }
    }
    switch (action) {
    case NR_WINDOW_SOURCE_ACTION_CLOSE: return 0x00d7u;
    case NR_WINDOW_SOURCE_ACTION_MINIMIZE: return '_';
    case NR_WINDOW_SOURCE_ACTION_MAXIMIZE: return 0x25a1u;
    default: return 0x25c7u;
    }
}

static int profile_order(int chrome, int index) {
    static const int mac[4] = {
        NR_WINDOW_SOURCE_ACTION_CLOSE, NR_WINDOW_SOURCE_ACTION_MINIMIZE,
        NR_WINDOW_SOURCE_ACTION_MAXIMIZE, NR_WINDOW_SOURCE_ACTION_BACKGROUND
    };
    static const int windows[4] = {
        NR_WINDOW_SOURCE_ACTION_MINIMIZE, NR_WINDOW_SOURCE_ACTION_MAXIMIZE,
        NR_WINDOW_SOURCE_ACTION_BACKGROUND, NR_WINDOW_SOURCE_ACTION_CLOSE
    };
    static const int gnome[4] = {
        NR_WINDOW_SOURCE_ACTION_BACKGROUND, NR_WINDOW_SOURCE_ACTION_MINIMIZE,
        NR_WINDOW_SOURCE_ACTION_MAXIMIZE, NR_WINDOW_SOURCE_ACTION_CLOSE
    };
    if (chrome == NR_WINDOW_SOURCE_CHROME_MAC) return mac[index];
    if (chrome == NR_WINDOW_SOURCE_CHROME_GNOME) return gnome[index];
    return windows[index];
}

int nrWindowSourcePresentationControls(
    const NrWindowSourcePresentationOptions *options,
    NrWindowSourceControl controls[4]) {
    if (!controls || !nrWindowSourcePresentationValid(options)) return -1;
    NrWindowSourceControl result[4];
    for (int i = 0; i < 4; ++i) {
        int action = options->chrome == NR_WINDOW_SOURCE_CHROME_CUSTOM
                   ? options->customOrder[i] : profile_order(options->chrome, i);
        int side = options->chrome == NR_WINDOW_SOURCE_CHROME_CUSTOM
                 ? options->customSide
                 : options->chrome == NR_WINDOW_SOURCE_CHROME_MAC
                 ? NR_WINDOW_SOURCE_SIDE_LEFT : NR_WINDOW_SOURCE_SIDE_RIGHT;
        result[i].action = action;
        result[i].glyph = options->chrome == NR_WINDOW_SOURCE_CHROME_CUSTOM
                        ? options->customGlyphs[i] : profile_glyph(options->chrome, action);
        result[i].color = action_color(action);
        result[i].index = i;
        result[i].side = side;
        result[i].width = options->controlWidth;
        result[i].height = options->controlHeight;
        const char *label = action_label(action);
        int j = 0;
        do {
            result[i].label[j] = label[j];
        } while (label[j++] != '\0' && j < 6);
    }
    for (int i = 0; i < 4; ++i) controls[i] = result[i];
    return 0;
}
