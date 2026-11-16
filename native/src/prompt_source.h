#ifndef NR_PROMPT_SOURCE_H
#define NR_PROMPT_SOURCE_H

#include <stddef.h>
#include <stdint.h>

/* Pure historical Atelier prompt layout/paint interface. The caller owns and
 * retains the borrowed scalar/status buffers for the duration of each call. */
typedef enum {
    NR_PROMPT_SOURCE_MARQUEE = 0,
    NR_PROMPT_SOURCE_GROW = 1,
    NR_PROMPT_SOURCE_VIM_INLINE = 2,
    NR_PROMPT_SOURCE_VIM_FULL = 3
} NrPromptSourceMode;

typedef enum {
    NR_PROMPT_SOURCE_BORDER_NONE = 0,
    NR_PROMPT_SOURCE_BORDER_ROUNDED = 1,
    NR_PROMPT_SOURCE_BORDER_SQUARE = 2,
    NR_PROMPT_SOURCE_BORDER_DOUBLE = 3,
    NR_PROMPT_SOURCE_BORDER_HEAVY = 4
} NrPromptSourceBorder;

typedef enum {
    NR_PROMPT_SOURCE_VIM_NORMAL = 0,
    NR_PROMPT_SOURCE_VIM_INSERT = 1,
    NR_PROMPT_SOURCE_VIM_VISUAL = 2,
    NR_PROMPT_SOURCE_VIM_COMMAND = 3
} NrPromptSourceVimState;

typedef enum {
    NR_PROMPT_SOURCE_PAINT_PANEL = 1,
    NR_PROMPT_SOURCE_PAINT_SELECTION = 2,
    NR_PROMPT_SOURCE_PAINT_CURSOR = 3,
    NR_PROMPT_SOURCE_PAINT_CHROME = 4,
    NR_PROMPT_SOURCE_PAINT_ACTION = 5,
    NR_PROMPT_SOURCE_PAINT_AUTHORED = 6
} NrPromptSourcePaintKind;

typedef enum {
    NR_PROMPT_SOURCE_OWNER_BODY = 1,
    NR_PROMPT_SOURCE_OWNER_MINIMIZE = 2,
    NR_PROMPT_SOURCE_OWNER_MAXIMIZE = 3,
    NR_PROMPT_SOURCE_OWNER_CLOSE = 4,
    NR_PROMPT_SOURCE_OWNER_RESTORE = 5,
    NR_PROMPT_SOURCE_OWNER_RESIZE = 6
} NrPromptSourceOwner;

/* Background callback semantics: PANEL mixes RGB with the destination's
 * foreground and background at alpha and clears any nondecorative source glyph
 * to a space while retaining decorative glyph/owner; SELECTION blends only
 * the background at alpha 0.8; CURSOR blends only the existing cell background
 * at alpha 0.18. Glyph callbacks are opaque source writes, except the callback
 * alpha field remains explicit for compositor uniformity. A CURSOR glyph write
 * is the RC2 vertical bar for an empty/decorative caret cell. */

typedef struct {
    double alpha;
    uint32_t background, foreground, accent, selectionColor;
    int border;
    int64_t paddingX, paddingY, margin, minRows, maxRows, inlineRows, inlineWidth;
    int lineNumbers, active, selected;
    double hueStep, hueSpeed;
    int64_t huePeriodMs;
    uint32_t maxChars;
} NrPromptSourceOptions;

typedef struct {
    const uint32_t *scalars;
    size_t scalarCount;
    size_t caret;
    size_t selectionStart, selectionEnd;
    int hasSelection;
    const uint32_t *statusScalars;
    size_t statusCount;
    int64_t width, height;
    uint64_t timeMs;
    int mode;
    int vimState;
    int minimizedRestoreMode; /* 0 absent, 1 inline, 2 fullscreen */
    NrPromptSourceOptions options;
} NrPromptSourceInput;

typedef struct {
    int32_t rectX, rectY, rectWidth, rectHeight;
    int32_t innerX, innerY, innerWidth, innerHeight;
    int32_t caretX, caretY;
    int32_t visibleRows, border, numberWidth, prefix;
    int32_t top, offset, extraRows, sceneHeight;
    int32_t full, vim;
} NrPromptSourceLayout;

typedef void (*NrPromptSourceBackgroundSink)(void *context, int32_t x, int32_t y,
                                             uint32_t rgb, double alpha,
                                             int kind, int owner);
typedef void (*NrPromptSourceGlyphSink)(void *context, int32_t x, int32_t y,
                                         uint32_t scalar, uint32_t foreground,
                                         double alpha, int kind, int owner);

typedef struct {
    void *context;
    NrPromptSourceBackgroundSink background;
    NrPromptSourceGlyphSink glyph;
} NrPromptSourceSink;

/* Return 0 on success, -1 on invalid input, unsupported source values, or a
 * coordinate result that cannot be represented in the public layout. Failure
 * leaves `layout` untouched and never invokes paint callbacks. */
int nrPromptSourceLayout(const NrPromptSourceInput *input,
                         NrPromptSourceLayout *layout);
int nrPromptSourcePaint(const NrPromptSourceInput *input,
                        const NrPromptSourceLayout *layout,
                        NrPromptSourceSink sink);

#endif
