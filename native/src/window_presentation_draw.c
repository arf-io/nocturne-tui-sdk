#include "internal.h"
#include "stage_native.h"
#include "window_presentation.h"

#include <limits.h>

static uint32_t action_family(int action) {
    switch (action) {
    case NR_WINDOW_SOURCE_ACTION_CLOSE: return NR_ID_CLOSE;
    case NR_WINDOW_SOURCE_ACTION_MINIMIZE: return NR_ID_MIN;
    case NR_WINDOW_SOURCE_ACTION_MAXIMIZE: return NR_ID_MAX;
    default: return NR_ID_WINDOW_RETURN;
    }
}

enum {
    SOURCE_NODE_KIND = 0, SOURCE_NODE_ID = 1, SOURCE_NODE_X = 2,
    SOURCE_NODE_Y = 3, SOURCE_NODE_WIDTH = 4, SOURCE_NODE_HEIGHT = 5,
    SOURCE_NODE_STATE = 6, SOURCE_NODE_FG = 12, SOURCE_NODE_BG = 13,
    SOURCE_NODE_FG_OPACITY = 14, SOURCE_NODE_BG_OPACITY = 15,
    SOURCE_NODE_STYLE = 16, SOURCE_NODE_TEXT_OFFSET = 17,
    SOURCE_NODE_TEXT_COUNT = 18, SOURCE_NODE_HUE_STEP = 21,
    SOURCE_NODE_HUE_SPEED = 22, SOURCE_NODE_SATURATION = 26,
    SOURCE_NODE_BRIGHTNESS = 27, SOURCE_NODE_ZOOM = 30
};

static int draw_source_button(NrContext *context,
    const NrWindowPresentationControlRect *rect,
    const NrWindowSourceControl *control, uint32_t hitId, uint32_t owner) {
    int32_t node[32] = {0};
    uint32_t text[16];
    uint32_t count = 0;
    node[SOURCE_NODE_KIND] = 3;
    node[SOURCE_NODE_ID] = 0;
    node[SOURCE_NODE_X] = rect->x;
    node[SOURCE_NODE_Y] = rect->y;
    node[SOURCE_NODE_WIDTH] = rect->width;
    node[SOURCE_NODE_HEIGHT] = rect->height;
    node[SOURCE_NODE_STATE] = 0;
    node[SOURCE_NODE_FG] = (int32_t)control->color;
    node[SOURCE_NODE_BG] = 0x1e2938;
    node[SOURCE_NODE_FG_OPACITY] = 1000;
    node[SOURCE_NODE_BG_OPACITY] = 880;
    node[SOURCE_NODE_STYLE] = 0;
    node[SOURCE_NODE_TEXT_OFFSET] = 0;
    text[count++] = control->glyph;
    text[count++] = ' ';
    for (int i = 0; control->label[i] && count < sizeof(text) / sizeof(text[0]); ++i)
        text[count++] = (uint8_t)control->label[i];
    node[SOURCE_NODE_TEXT_COUNT] = (int32_t)count;
    node[SOURCE_NODE_HUE_STEP] = 17;
    node[SOURCE_NODE_HUE_SPEED] = 24;
    node[SOURCE_NODE_SATURATION] = 620;
    node[SOURCE_NODE_BRIGHTNESS] = 830;
    node[SOURCE_NODE_ZOOM] = 1;
    return nrSourceStageDrawTransient(context, node, text, count, owner, hitId);
}

int nrWindowPresentationDrawTheatreToolbar(NrContext *context, int frameWidth,
    const NrWindowSourcePresentationOptions *options, double alpha, uint32_t targetId) {
    const State *state = context ? nrView(context) : NULL;
    if (!context || !context->cells || !context->characterIndices ||
        !context->characterOwners || !state || frameWidth < 1 ||
        state->width > INT_MAX || frameWidth != (int)state->width ||
        targetId < 1 || targetId > 65535 ||
        alpha != alpha || alpha < 0 || alpha > 1 ||
        !nrWindowSourcePresentationValid(options)) return -1;
    NrWindowPresentationControlRect rects[4];
    NrWindowSourceControl controls[4];
    if (nrWindowPresentationControlRects(frameWidth, options, rects) ||
        nrWindowSourcePresentationControls(options, controls)) return -1;

    const uint32_t owner = (2u << 16) | targetId;
    for (int i = 0; i < 4; ++i) {
        const NrWindowPresentationControlRect *rect = &rects[i];
        const NrWindowSourceControl *control = &controls[i];
        uint32_t hitId = action_family(control->action) | targetId;
        if (draw_source_button(context, rect, control, hitId, owner)) return -1;
    }
    (void)alpha;
    return 0;
}

