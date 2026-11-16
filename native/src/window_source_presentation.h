#ifndef NR_WINDOW_SOURCE_PRESENTATION_H
#define NR_WINDOW_SOURCE_PRESENTATION_H

#include <stdint.h>

typedef enum {
    NR_WINDOW_SOURCE_CHROME_MAC = 0,
    NR_WINDOW_SOURCE_CHROME_WINDOWS = 1,
    NR_WINDOW_SOURCE_CHROME_GNOME = 2,
    NR_WINDOW_SOURCE_CHROME_CUSTOM = 3
} NrWindowSourceChrome;

typedef enum {
    NR_WINDOW_SOURCE_ACTION_CLOSE = 0,
    NR_WINDOW_SOURCE_ACTION_MINIMIZE = 1,
    NR_WINDOW_SOURCE_ACTION_MAXIMIZE = 2,
    NR_WINDOW_SOURCE_ACTION_BACKGROUND = 3
} NrWindowSourceAction;

typedef enum {
    NR_WINDOW_SOURCE_SIDE_LEFT = 0,
    NR_WINDOW_SOURCE_SIDE_RIGHT = 1
} NrWindowSourceSide;

typedef struct {
    double opacity, depthFade;
    int chrome, controlWidth, controlHeight, customSide;
    int customOrder[4];
    uint32_t customGlyphs[4];
} NrWindowSourcePresentationOptions;

typedef struct {
    int action;
    uint32_t glyph, color;
    int index, side, width, height;
    char label[6];
} NrWindowSourceControl;

/* Values and bounds are the original RC2 WindowManager defaults. */
void nrWindowSourcePresentationDefaults(NrWindowSourcePresentationOptions *options);
int nrWindowSourcePresentationValid(const NrWindowSourcePresentationOptions *options);

/* The source uses world-space window z, fades only positive depth, and keeps
 * at least 20% of the configured opacity. Returns -1 for invalid input. */
int nrWindowSourcePresentationOpacity(
    const NrWindowSourcePresentationOptions *options,
    double worldZ, double *opacity);

/* Emits controls in source order. Each descriptor is both the decoration
 * glyph and the source hit-target metadata. Returns -1 without writing output
 * when options or the output pointer are invalid. */
int nrWindowSourcePresentationControls(
    const NrWindowSourcePresentationOptions *options,
    NrWindowSourceControl controls[4]);

#endif
