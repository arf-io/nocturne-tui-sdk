#include "internal.h"

#include <float.h>
#include <limits.h>

static int finite_number(double value) {
    return value == value && value <= DBL_MAX && value >= -DBL_MAX;
}

static double truncate_number(double value) {
    return value < 0 ? -nrFloor(-value) : nrFloor(value);
}

enum {
    NR_PROMPT_ACTION_NONE = -1,
    NR_PROMPT_ACTION_MINIMIZE = -2,
    NR_PROMPT_ACTION_MAXIMIZE = -3,
    NR_PROMPT_ACTION_CLOSE = -4,
    NR_PROMPT_ACTION_RESTORE = -5,
    NR_PROMPT_ACTION_RESIZE = -6
};

static int fail(NrContext *c, const char *message) {
    size_t n = strlen(message);
    if (n > sizeof(c->error) - 1) n = sizeof(c->error) - 1;
    memcpy(c->error, message, n);
    c->error[n] = 0;
    return -1;
}

static int field_number(const Json *j, const char *key, double *value,
                        double minimum, double maximum) {
    int token = nrField(j, 0, key);
    if (token < 0) return 1;
    double candidate;
    if (!nrNumber(j, token, &candidate) || !finite_number(candidate) ||
        candidate < minimum || candidate > maximum) return 0;
    *value = candidate;
    return 1;
}

static int field_integer(const Json *j, const char *key, int64_t *value,
                         int64_t minimum, int64_t maximum) {
    int token = nrField(j, 0, key);
    if (token < 0) return 1;
    double candidate;
    if (!nrNumber(j, token, &candidate) || !finite_number(candidate) ||
        candidate < (double)minimum || candidate > (double)maximum ||
        candidate != truncate_number(candidate)) return 0;
    *value = (int64_t)candidate;
    return 1;
}

static int field_boolean(const Json *j, const char *key, int *value) {
    int token = nrField(j, 0, key);
    return token < 0 || nrBoolean(j, token, value);
}

static int field_color(const Json *j, const char *key, uint32_t *value) {
    int token = nrField(j, 0, key);
    if (token < 0) return 1;
    char text[16];
    if (nrString(j, token, text, sizeof(text)) != 7 || text[0] != '#') return 0;
    uint32_t color = 0;
    for (int i = 1; i < 7; i++) {
        unsigned char ch = (unsigned char)text[i];
        int digit = ch >= '0' && ch <= '9' ? ch - '0' :
            ch >= 'a' && ch <= 'f' ? ch - 'a' + 10 :
            ch >= 'A' && ch <= 'F' ? ch - 'A' + 10 : -1;
        if (digit < 0) return 0;
        color = (color << 4) | (uint32_t)digit;
    }
    *value = color;
    return 1;
}

static int field_choice(const Json *j, const char *key, const char *choices,
                        int *value) {
    int token = nrField(j, 0, key);
    if (token < 0) return 1;
    char text[64];
    if (nrString(j, token, text, sizeof(text)) < 0) return 0;
    const char *at = choices;
    for (int i = 0; *at; i++) {
        const char *end = at;
        while (*end && *end != ' ') end++;
        if (strlen(text) == (size_t)(end - at) && !memcmp(text, at, (size_t)(end - at))) {
            *value = i;
            return 1;
        }
        at = *end ? end + 1 : end;
    }
    return 0;
}

static void source_defaults(NrPromptSourceOptions *o) {
    memset(o, 0, sizeof(*o));
    o->alpha = .32;
    o->background = 0x10161e;
    o->foreground = 0xdedbd2;
    o->accent = 0x8ccfc4;
    o->selectionColor = 0x385763;
    o->border = NR_PROMPT_SOURCE_BORDER_ROUNDED;
    o->paddingX = 1;
    o->paddingY = 0;
    o->margin = 1;
    o->minRows = 1;
    o->maxRows = 7;
    o->inlineRows = 12;
    o->inlineWidth = 88;
    o->lineNumbers = 1;
    o->active = 1;
    o->huePeriodMs = 1000;
    o->maxChars = 0;
}

static int framed_fields_valid(const State *s, const Prompt *p, const PromptFramed *f,
                               uint32_t width, uint32_t height) {
    if (!p || !f) return 0;
    if (!f->enabled) {
        const unsigned char *bytes = (const unsigned char *)f;
        for (size_t i = 0; i < sizeof(*f); i++) if (bytes[i]) return 0;
        return 1;
    }
    if (f->reserved || f->reserved2 || f->enabled > 1 ||
        f->vimState > NR_PROMPT_SOURCE_VIM_COMMAND ||
        f->minimizedRestoreMode > 2 || f->normalMode > 1) return 0;
    if (f->commandCount > 256 || f->searchCount > 255 || f->messageCount > 512 ||
        f->checkpointValid > 1 || f->checkpointCount > s->dynamicPrompt.capacity ||
        f->checkpointCaret > f->checkpointCount || f->checkpointMode > NR_PROMPT_SOURCE_VIM_FULL ||
        f->checkpointNormalMode > NR_PROMPT_SOURCE_GROW ||
        f->checkpointVimState > NR_PROMPT_SOURCE_VIM_COMMAND) return 0;
    for (uint32_t i = 0; i < f->commandCount; i++)
        if (f->command[i] > 0x10ffffu || (f->command[i] >= 0xd800u && f->command[i] <= 0xdfffu)) return 0;
    for (uint32_t i = f->commandCount; i < 256; i++) if (f->command[i]) return 0;
    for (uint32_t i = 0; i < f->searchCount; i++)
        if (f->search[i] > 0x10ffffu || (f->search[i] >= 0xd800u && f->search[i] <= 0xdfffu)) return 0;
    for (uint32_t i = f->searchCount; i < 256; i++) if (f->search[i]) return 0;
    for (uint32_t i = 0; i < f->messageCount; i++)
        if (f->message[i] > 0x10ffffu || (f->message[i] >= 0xd800u && f->message[i] <= 0xdfffu)) return 0;
    for (uint32_t i = f->messageCount; i < 512; i++) if (f->message[i]) return 0;
    if (f->checkpointValid) {
        if (f->checkpointOptions.maxChars && f->checkpointCount > f->checkpointOptions.maxChars) return 0;
        NrPromptSourceInput saved;
        memset(&saved, 0, sizeof(saved));
        uint32_t emptyScalar = 0;
        saved.width = width; saved.height = height;
        saved.mode = (int)f->checkpointMode;
        saved.vimState = (int)f->checkpointVimState;
        saved.scalars = &emptyScalar;
        saved.options = f->checkpointOptions;
        if (nrPromptSourceLayout(&saved, &(NrPromptSourceLayout){0}) < 0) return 0;
        for (uint32_t i = 0; i < f->checkpointCount; i++)
            if (s->dynamicPrompt.checkpoint[i] > 0x10ffffu ||
                (s->dynamicPrompt.checkpoint[i] >= 0xd800u && s->dynamicPrompt.checkpoint[i] <= 0xdfffu)) return 0;
        for (uint32_t i = f->checkpointCount; i < s->dynamicPrompt.capacity; i++)
            if (s->dynamicPrompt.checkpoint[i]) return 0;
    } else {
        NrPromptSourceOptions clearedOptions;
        memset(&clearedOptions, 0, sizeof(clearedOptions));
        if (f->checkpointCount || f->checkpointCaret || f->checkpointMode ||
            f->checkpointNormalMode || f->checkpointVimState ||
            memcmp(&f->checkpointOptions, &clearedOptions, sizeof(f->checkpointOptions))) return 0;
        for (uint32_t i = 0; i < s->dynamicPrompt.capacity; i++) if (s->dynamicPrompt.checkpoint[i]) return 0;
    }
    NrPromptSourceInput input;
    memset(&input, 0, sizeof(input));
    input.width = width;
    input.height = height;
    input.mode = p->mode;
    input.vimState = (int)f->vimState;
    input.minimizedRestoreMode = (int)f->minimizedRestoreMode;
    input.options = f->options;
    uint32_t emptyScalar = 0;
    input.scalars = &emptyScalar;
    return nrPromptSourceLayout(&input, &(NrPromptSourceLayout){0}) == 0 &&
        (f->minimizedRestoreMode == 0 || p->mode <= NR_PROMPT_SOURCE_GROW) &&
        p->mode >= NR_PROMPT_SOURCE_MARQUEE && p->mode <= NR_PROMPT_SOURCE_VIM_FULL &&
        f->options.alpha == p->alpha && f->options.border == p->border &&
        f->options.minRows == p->minRows && f->options.maxRows == p->maxRows &&
        f->options.active == p->active;
}

static int source_only_fields_present(const Json *j) {
    static const char *const fields[] = {
        "background", "foreground", "accent", "selectionColor", "paddingX",
        "paddingY", "margin", "inlineRows", "inlineWidth", "lineNumbers",
        "selected", "hueStep", "hueSpeed", "huePeriodMs", "maxChars"
    };
    for (size_t i = 0; i < sizeof(fields) / sizeof(fields[0]); i++)
        if (nrField(j, 0, fields[i]) >= 0) return 1;
    return 0;
}

static int parse_source_options(NrContext *c, const Json *j,
                                NrPromptSourceOptions *o) {
    int border = o->border;
    int64_t integer = 0;
    int flag;
    if (!field_number(j, "alpha", &o->alpha, 0, 1) ||
        !field_color(j, "background", &o->background) ||
        !field_color(j, "foreground", &o->foreground) ||
        !field_color(j, "accent", &o->accent) ||
        !field_color(j, "selectionColor", &o->selectionColor) ||
        !field_choice(j, "border", "none rounded square double heavy", &border))
        return fail(c, "Invalid framed prompt color, alpha, or border");
    o->border = border;
#define PROMPT_INT(name, member, low, high) do { \
    integer = o->member; \
    if (!field_integer(j, name, &integer, low, high)) return fail(c, "Invalid framed prompt integer: " name); \
    o->member = integer; \
} while (0)
    PROMPT_INT("paddingX", paddingX, 0, 8);
    PROMPT_INT("paddingY", paddingY, 0, 4);
    PROMPT_INT("margin", margin, 0, 6);
    PROMPT_INT("minRows", minRows, 1, 24);
    PROMPT_INT("maxRows", maxRows, 1, 60);
    PROMPT_INT("inlineRows", inlineRows, 5, 80);
    PROMPT_INT("inlineWidth", inlineWidth, 24, 240);
    PROMPT_INT("huePeriodMs", huePeriodMs, 1, 120000);
#undef PROMPT_INT
    integer = o->maxChars;
    if (!field_integer(j, "maxChars", &integer, 0, INT32_MAX))
        return fail(c, "Invalid framed prompt integer: maxChars");
    o->maxChars = (uint32_t)integer;
    if (!field_number(j, "hueStep", &o->hueStep, -360, 360) ||
        !field_number(j, "hueSpeed", &o->hueSpeed, -360, 360))
        return fail(c, "Invalid framed prompt hue motion");
    flag = o->lineNumbers;
    if (!field_boolean(j, "lineNumbers", &flag)) return fail(c, "lineNumbers must be Boolean");
    o->lineNumbers = flag;
    flag = o->active;
    if (!field_boolean(j, "active", &flag)) return fail(c, "active must be Boolean");
    o->active = flag;
    flag = o->selected;
    if (!field_boolean(j, "selected", &flag)) return fail(c, "selected must be Boolean");
    o->selected = flag;
    if (o->minRows > o->maxRows) return fail(c, "Framed prompt row bounds");
    return 0;
}

int nrPromptFramedCommand(NrContext *c, State *s, const Json *j) {
    if (!c) return -1;
    if (!s || !j || !nrAllowed(j, 0,
        "op mode alpha minRows maxRows border padding active layout ambiguousWidth direction presentation "
        "background foreground accent selectionColor paddingX paddingY margin inlineRows inlineWidth "
        "lineNumbers selected hueStep hueSpeed huePeriodMs maxChars"))
        return fail(c, "Unknown or unsupported prompt field");

    PromptFramed framedCandidate = s->promptFramed;
    int presentationLayout = s->promptPresentation.layout;
    int presentationAmbiguous = s->promptPresentation.ambiguous;
    Prompt *p = &s->promptDocument;
    PromptFramed *framed = &framedCandidate;
    int presentation = framed->enabled ? 1 : 0;
    int presentationToken = nrField(j, 0, "presentation");
    if ((presentationToken >= 0 || source_only_fields_present(j)) &&
        s->schema < NR_STATE_SCHEMA_PROMPT_FRAMED)
        return fail(c, "Framed prompt requires current state schema");
    if (presentationToken >= 0 && !field_choice(j, "presentation", "compact framed", &presentation))
        return fail(c, "Prompt presentation must be compact or framed");
    const int explicitlyCompact = presentationToken >= 0 && presentation == 0;
    if (explicitlyCompact && source_only_fields_present(j))
        return fail(c, "Framed-only prompt controls require framed presentation");
    if (!presentation && presentationToken < 0 && source_only_fields_present(j))
        return fail(c, "Framed-only prompt controls require framed presentation");

    if (presentation) {
        if (!framed->enabled) {
            memset(framed, 0, sizeof(*framed));
            source_defaults(&framed->options);
            framed->enabled = 1;
            framed->normalMode = p->mode <= 1 ? (uint32_t)p->mode : 0;
            framed->vimState = p->vimMode ? NR_PROMPT_SOURCE_VIM_INSERT : NR_PROMPT_SOURCE_VIM_NORMAL;
            p->alpha = framed->options.alpha;
            p->border = framed->options.border;
            p->minRows = (int)framed->options.minRows;
            p->maxRows = (int)framed->options.maxRows;
            p->active = framed->options.active;
        }
        framed->enabled = 1;
    } else if (explicitlyCompact) {
        memset(framed, 0, sizeof(*framed));
    }

    int oldMode = p->mode;
    int mode = oldMode;
    if (!field_choice(j, "mode", "marquee grow vim-inline vim-full", &mode))
        return fail(c, "Invalid prompt mode");
    int modeExplicit = nrField(j, 0, "mode") >= 0;
    if (modeExplicit) {
        if (framed->enabled) {
            if (mode <= NR_PROMPT_SOURCE_GROW) framed->normalMode = (uint32_t)mode;
            else if (oldMode < NR_PROMPT_SOURCE_VIM_INLINE) framed->normalMode = (uint32_t)oldMode;
            framed->minimizedRestoreMode = 0;
        }
        /* Source setMode examines the old mode: leaving Vim retains its
         * command/insert state, while entering Vim from a normal view resets
         * it. The command string survives both transitions. */
        if (oldMode < NR_PROMPT_SOURCE_VIM_INLINE) {
            p->vimMode = 0;
            framed->vimState = NR_PROMPT_SOURCE_VIM_NORMAL;
        }
        p->mode = mode;
    }

    double alpha = p->alpha;
    int64_t minRows = p->minRows, maxRows = p->maxRows;
    int border = p->border, padding = p->padding, active = p->active;
    int64_t paddingValue = padding, ambiguousValue;
    if (!field_number(j, "alpha", &alpha, 0, 1) ||
        !field_integer(j, "minRows", &minRows, 1, NR_LAYOUT_MAX) ||
        !field_integer(j, "maxRows", &maxRows, 1, NR_LAYOUT_MAX) ||
        !field_choice(j, "border", "none rounded square double heavy", &border) ||
        !field_integer(j, "padding", &paddingValue, 0, 4) ||
        !field_boolean(j, "active", &active)) return fail(c, "Invalid prompt shared control");
    padding = (int)paddingValue;
    if (minRows > maxRows) return fail(c, "Prompt row bounds");
    p->alpha = alpha;
    p->minRows = (int)minRows;
    p->maxRows = (int)maxRows;
    p->border = border;
    p->padding = padding;
    p->active = active;
    if (framed->enabled) {
        framed->options.alpha = p->alpha;
        framed->options.border = p->border;
        framed->options.minRows = p->minRows;
        framed->options.maxRows = p->maxRows;
        framed->options.active = p->active;
        if (nrField(j, 0, "padding") >= 0) {
            framed->options.paddingX = padding;
            framed->options.paddingY = padding;
        }
        if (parse_source_options(c, j, &framed->options) < 0) return -1;
        if (framed->options.maxChars && p->count > (int)framed->options.maxChars)
            return fail(c, "maxChars below current draft");
        /* Shared controls are represented once in Prompt and serialized from
         * there; source-only axes remain independent. */
        framed->options.alpha = p->alpha;
        framed->options.border = p->border;
        framed->options.minRows = p->minRows;
        framed->options.maxRows = p->maxRows;
        framed->options.active = p->active;
    }

    if (nrField(j, 0, "layout") >= 0 || nrField(j, 0, "ambiguousWidth") >= 0 ||
        nrField(j, 0, "direction") >= 0) {
        if (s->schema < NR_STATE_SCHEMA_PROMPT_PRESENTATION)
            return fail(c, "Prompt presentation requires current schema");
        int layout = presentationLayout & 3;
        int oldBidi = layout == 2;
        int direction = oldBidi ? (presentationLayout >> 2) : 2;
        int ambiguous = presentationAmbiguous ? presentationAmbiguous : 1;
        ambiguousValue = ambiguous;
        if (!field_choice(j, "layout", "scalar grapheme bidi", &layout) ||
            !field_choice(j, "direction", "ltr rtl auto", &direction) ||
            !field_integer(j, "ambiguousWidth", &ambiguousValue, 1, 2))
            return fail(c, "Invalid prompt presentation setting");
        ambiguous = (int)ambiguousValue;
        if ((layout != 2 && nrField(j, 0, "direction") >= 0) ||
            (layout == 2 && s->schema < NR_STATE_SCHEMA_BIDI_PROMPT))
            return fail(c, "Bidi direction requires current bidi prompt schema");
        presentationLayout = layout == 2 ? 2 + (direction << 2) : layout;
        presentationAmbiguous = ambiguous;
    }

    if (!framed_fields_valid(s,p, framed, s->width, s->height))
        return fail(c, "Invalid retained framed prompt state");
    s->promptFramed = framedCandidate;
    s->promptPresentation.layout = presentationLayout;
    s->promptPresentation.ambiguous = presentationAmbiguous;
    nrPointerRelease(s);
    return 0;
}

int nrPromptFramedValid(const State *s) {
    return s && framed_fields_valid(s,&s->promptDocument, &s->promptFramed, s->width, s->height);
}

int nrPromptFramedInput(const State *s, NrPromptSourceInput *input) {
    if (!s || !input || !s->promptFramed.enabled || !nrPromptFramedValid(s)) return -1;
    static const uint32_t defaultStatus[] = {
        'E','s','c',' ', 'N','O','R','M','A','L',' ',0x00b7,' ',
        'i',' ', 'I','N','S','E','R','T',' ',0x00b7,' ',
        ':','w',' ', 'c','h','e','c','k','p','o','i','n','t',' ',0x00b7,' ',
        ':','q',' ', 'c','l','o','s','e',' ', 'v','i','e','w',' ',0x00b7,' ',
        'd','r','a','g',' ',0x2198,' ', 'r','e','s','i','z','e'
    };
    memset(input, 0, sizeof(*input));
    input->scalars = s->promptDocument.glyphs;
    input->scalarCount = (size_t)s->promptDocument.count;
    input->caret = (size_t)s->promptDocument.caret;
    if (s->promptDocument.anchor >= 0 && s->promptDocument.anchor != s->promptDocument.caret) {
        input->hasSelection = 1;
        input->selectionStart = (size_t)(s->promptDocument.anchor < s->promptDocument.caret ? s->promptDocument.anchor : s->promptDocument.caret);
        input->selectionEnd = (size_t)(s->promptDocument.anchor > s->promptDocument.caret ? s->promptDocument.anchor : s->promptDocument.caret);
    }
    input->statusScalars = defaultStatus;
    input->statusCount = sizeof(defaultStatus) / sizeof(defaultStatus[0]);
    if (s->promptFramed.vimState == NR_PROMPT_SOURCE_VIM_COMMAND) {
        input->statusScalars = s->promptFramed.command;
        input->statusCount = s->promptFramed.commandCount;
    } else if (s->promptFramed.messageCount) {
        input->statusScalars = s->promptFramed.message;
        input->statusCount = s->promptFramed.messageCount;
    }
    input->width = s->width;
    input->height = s->height;
    input->timeMs = s->timeUs / 1000;
    input->mode = s->promptDocument.mode;
    input->vimState = s->promptDocument.mode >= NR_PROMPT_SOURCE_VIM_INLINE ?
        (s->promptDocument.vimMode ? NR_PROMPT_SOURCE_VIM_INSERT : (int)s->promptFramed.vimState) :
        (int)s->promptFramed.vimState;
    input->minimizedRestoreMode = (int)s->promptFramed.minimizedRestoreMode;
    input->options = s->promptFramed.options;
    /* Original history may restore a larger pre-configuration document.
     * Rendering does not authorize further insertions above the authored bound. */
    if(input->scalarCount>input->options.maxChars)input->options.maxChars=(uint32_t)input->scalarCount;
    return 0;
}

int nrPromptFramedLayout(const State *s, NrPromptSourceInput *input,
                         NrPromptSourceLayout *layout) {
    if (nrPromptFramedInput(s, input) < 0) return -1;
    return nrPromptSourceLayout(input, layout);
}

int nrPromptFramedActivate(NrContext *c, State *s, int action) {
    if (!c || !s || !s->promptFramed.enabled) return fail(c, "Framed prompt action is unavailable");
    Prompt *p = &s->promptDocument;
    PromptFramed *f = &s->promptFramed;
    if (action == NR_PROMPT_ACTION_RESIZE) return 0;
    if (action == NR_PROMPT_ACTION_MINIMIZE) {
        if (p->mode < NR_PROMPT_SOURCE_VIM_INLINE) return 0;
        f->minimizedRestoreMode = (uint32_t)p->mode;
        p->mode = (int)f->normalMode;
    } else if (action == NR_PROMPT_ACTION_MAXIMIZE) {
        if (p->mode < NR_PROMPT_SOURCE_VIM_INLINE) return 0;
        p->mode = p->mode == NR_PROMPT_SOURCE_VIM_FULL ? NR_PROMPT_SOURCE_VIM_INLINE : NR_PROMPT_SOURCE_VIM_FULL;
        f->minimizedRestoreMode = 0;
    } else if (action == NR_PROMPT_ACTION_CLOSE) {
        p->mode = (int)f->normalMode;
        p->vimMode = 0;
        p->anchor = -1;
        f->vimState = NR_PROMPT_SOURCE_VIM_NORMAL;
        f->minimizedRestoreMode = 0;
        memset(f->command, 0, sizeof(f->command));
        f->commandCount = 0;
    } else if (action == NR_PROMPT_ACTION_RESTORE) {
        int restoreFromNormalMode = p->mode < NR_PROMPT_SOURCE_VIM_INLINE;
        p->mode = f->minimizedRestoreMode ? (int)f->minimizedRestoreMode : NR_PROMPT_SOURCE_VIM_INLINE;
        if (restoreFromNormalMode) {
            f->vimState = NR_PROMPT_SOURCE_VIM_NORMAL;
            p->vimMode = 0;
        } else {
            p->vimMode = f->vimState == NR_PROMPT_SOURCE_VIM_INSERT;
        }
        f->minimizedRestoreMode = 0;
    } else return fail(c, "Unknown framed prompt action");
    p->revision++;
    nrPointerRelease(s);
    s->vimCount.count = 0;
    s->vimOperator.key = 0;
    return 0;
}

static int source_position(const NrPromptSourceInput *input,
                           const NrPromptSourceLayout *layout, size_t index,
                           int32_t *x, int32_t *y) {
    if (index > input->scalarCount) return 0;
    int64_t row = 0, col = 0;
    if (input->mode == NR_PROMPT_SOURCE_MARQUEE) {
        int64_t at = (int64_t)layout->innerX + (int64_t)index - layout->offset;
        if (at < INT32_MIN || at > INT32_MAX || layout->innerY < INT32_MIN || layout->innerY > INT32_MAX) return 0;
        *x = (int32_t)at;
        *y = layout->innerY;
        return 1;
    }
    for (size_t i = 0; i < index; i++) {
        if (col == layout->innerWidth) { row++; col = 0; }
        if (input->scalars[i] == '\n') { row++; col = 0; }
        else col++;
    }
    if (col == layout->innerWidth) { row++; col = 0; }
    int64_t sx = (int64_t)layout->innerX + col;
    int64_t sy = (int64_t)layout->innerY + row - layout->top;
    if (sx < INT32_MIN || sx > INT32_MAX || sy < INT32_MIN || sy > INT32_MAX) return 0;
    *x = (int32_t)sx;
    *y = (int32_t)sy;
    return 1;
}

void nrPromptFramedCoordinate(const State *s, int index, int *x, int *y) {
    if (!s || !x || !y) return;
    NrPromptSourceInput input;
    NrPromptSourceLayout layout;
    if (nrPromptFramedLayout(s, &input, &layout) < 0) return;
    int32_t sx, sy;
    if (index < 0) index = 0;
    if ((size_t)index > input.scalarCount) index = (int)input.scalarCount;
    if (source_position(&input, &layout, (size_t)index, &sx, &sy)) { *x = sx; *y = sy; }
}

int nrPromptFramedHit(const State *s, int x, int y) {
    if (!s || !s->promptFramed.enabled) return NR_PROMPT_ACTION_NONE;
    NrPromptSourceInput input;
    NrPromptSourceLayout layout;
    if (nrPromptFramedLayout(s, &input, &layout) < 0) return NR_PROMPT_ACTION_NONE;
    if (layout.vim && y == layout.rectY) {
        int bx = layout.rectX + layout.rectWidth - 17;
        if (x >= bx && x < bx + 5) return NR_PROMPT_ACTION_MINIMIZE;
        if (x >= bx + 5 && x < bx + 10) return NR_PROMPT_ACTION_MAXIMIZE;
        if (x >= bx + 10 && x < bx + 15) return NR_PROMPT_ACTION_CLOSE;
    }
    if (input.minimizedRestoreMode && !layout.vim && y == layout.rectY &&
        x >= layout.rectX + 2 && x < layout.rectX + 17) return NR_PROMPT_ACTION_RESTORE;
    if (layout.vim && y == layout.rectY + layout.rectHeight - 1 &&
        x >= layout.rectX + layout.rectWidth - 3 && x < layout.rectX + layout.rectWidth - 1)
        return NR_PROMPT_ACTION_RESIZE;
    if (x < layout.rectX || x >= (int64_t)layout.rectX + layout.rectWidth ||
        y < layout.rectY || y >= (int64_t)layout.rectY + layout.rectHeight)
        return NR_PROMPT_ACTION_NONE;
    int best = s->promptDocument.caret;
    int bestDistance = INT_MAX;
    int64_t row = 0, col = 0;
    size_t first = input.mode == NR_PROMPT_SOURCE_MARQUEE ? (size_t)layout.offset : 0;
    size_t last = input.scalarCount;
    if (input.mode == NR_PROMPT_SOURCE_MARQUEE && (uint64_t)layout.offset + (uint64_t)layout.innerWidth < last)
        last = (size_t)((uint64_t)layout.offset + (uint64_t)layout.innerWidth);
    for (size_t i = first; i <= input.scalarCount; i++) {
        int32_t sx, sy;
        if (input.mode == NR_PROMPT_SOURCE_MARQUEE) {
            if (i > last) break;
            int64_t px = (int64_t)layout.innerX + (int64_t)i - layout.offset;
            if (px < INT32_MIN || px > INT32_MAX) continue;
            sx = (int32_t)px;
            sy = layout.innerY;
        } else {
            if (col == layout.innerWidth) { row++; col = 0; }
            int64_t px = (int64_t)layout.innerX + col;
            int64_t py = (int64_t)layout.innerY + row - layout.top;
            if (px < INT32_MIN || px > INT32_MAX || py < INT32_MIN || py > INT32_MAX) continue;
            sx = (int32_t)px;
            sy = (int32_t)py;
        }
        int visible = input.mode == NR_PROMPT_SOURCE_MARQUEE ?
            sx >= layout.innerX && sx < layout.innerX + layout.innerWidth :
            sy >= layout.innerY && sy < layout.innerY + layout.visibleRows;
        if (visible && (input.mode != NR_PROMPT_SOURCE_MARQUEE || i <= last)) {
            int64_t dx = (int64_t)sx - x, dy = (int64_t)sy - y;
            int64_t wideDistance = (dy < 0 ? -dy : dy) * 1000 + (dx < 0 ? -dx : dx);
            int distance = wideDistance > INT_MAX ? INT_MAX : (int)wideDistance;
            if (distance < bestDistance) { best = (int)i; bestDistance = distance; }
        }
        if (input.mode != NR_PROMPT_SOURCE_MARQUEE && i < input.scalarCount) {
            if (input.scalars[i] == '\n') { row++; col = 0; }
            else col++;
        }
    }
    return best;
}

static uint32_t owner_for_role(int role) {
    switch (role) {
        case NR_PROMPT_SOURCE_OWNER_MINIMIZE: return (11u << 16);
        case NR_PROMPT_SOURCE_OWNER_MAXIMIZE: return (12u << 16);
        case NR_PROMPT_SOURCE_OWNER_CLOSE: return (13u << 16);
        case NR_PROMPT_SOURCE_OWNER_RESTORE: return (14u << 16);
        case NR_PROMPT_SOURCE_OWNER_RESIZE: return (15u << 16);
        default: return (10u << 16);
    }
}

typedef struct {
    NrContext *context;
    const State *state;
    const NrPromptSourceInput *input;
    NrPromptSourceLayout layout;
    size_t nextIndex;
    int64_t row, col;
} PromptSinkContext;

static int source_decorative(uint32_t glyph) {
    return glyph == ' ' || glyph == 0x2580 || glyph == 0x2584 || glyph == 0x258c ||
        glyph == 0x2590 || (glyph >= 0x2800 && glyph <= 0x28ff);
}

static void source_background(void *opaque, int32_t x, int32_t y, uint32_t rgb,
                             double alpha, int kind, int owner) {
    PromptSinkContext *sink = opaque;
    NrContext *c = sink->context;
    const State *s = sink->state;
    if (!nrInClip(c, x, y) || x < 0 || y < 0 || x >= (int)s->width || y >= (int)s->height) return;
    if(kind==NR_PROMPT_SOURCE_PAINT_CURSOR&&s->promptAppearance.cursorConfigured)return;
    size_t at = (size_t)y * s->width + (unsigned)x;
    NrCell *cell = &c->cells[at];
    if (kind == NR_PROMPT_SOURCE_PAINT_PANEL) {
        uint32_t foreground = cell->foreground;
        nrCellBackground(c, x, y, rgb, alpha);
        cell->foreground = nrMix(foreground, rgb, alpha);
        if (!source_decorative(cell->glyph)) {
            cell->glyph = ' ';
            cell->id = NR_ID_PROMPT;
            c->characterIndices[at] = UINT32_MAX;
            c->characterOwners[at] = owner_for_role(owner);
        }
    } else if (kind == NR_PROMPT_SOURCE_PAINT_SELECTION || kind == NR_PROMPT_SOURCE_PAINT_CURSOR) {
        nrCellBackground(c, x, y, rgb, alpha);
    }
}

static uint32_t source_index_at(PromptSinkContext *sink, int x, int y) {
    const NrPromptSourceInput *input = sink->input;
    const NrPromptSourceLayout *layout = &sink->layout;
    while (sink->nextIndex < input->scalarCount) {
        size_t i = sink->nextIndex++;
        int64_t sx, sy;
        if (input->mode == NR_PROMPT_SOURCE_MARQUEE) {
            sx = (int64_t)layout->innerX + (int64_t)i - layout->offset;
            sy = layout->innerY;
        } else {
            if (sink->col == layout->innerWidth) { sink->row++; sink->col = 0; }
            sx = (int64_t)layout->innerX + sink->col;
            sy = (int64_t)layout->innerY + sink->row - layout->top;
        }
        uint32_t scalar = input->scalars[i];
        if (input->mode != NR_PROMPT_SOURCE_MARQUEE) {
            if (scalar == '\n') { sink->row++; sink->col = 0; continue; }
            sink->col++;
        }
        if (sx == x && sy == y) return (uint32_t)i;
    }
    return UINT32_MAX;
}

static void source_glyph(void *opaque, int32_t x, int32_t y, uint32_t glyph,
                         uint32_t foreground, double alpha, int kind, int owner) {
    PromptSinkContext *sink = opaque;
    NrContext *c = sink->context;
    const State *s = sink->state;
    if (!nrInClip(c, x, y)) return;
    if(kind==NR_PROMPT_SOURCE_PAINT_CURSOR&&s->promptAppearance.cursorConfigured)return;
    uint32_t previous = c->characterOwner;
    c->characterOwner = owner_for_role(owner);
    uint32_t index = kind == NR_PROMPT_SOURCE_PAINT_AUTHORED ? source_index_at(sink, x, y) : UINT32_MAX;
    nrIndexedGlyph(c, x, y, glyph, foreground, alpha, NR_ID_PROMPT, index);
    if (kind == NR_PROMPT_SOURCE_PAINT_ACTION) {
        size_t at = (size_t)y * s->width + (unsigned)x;
        uint32_t tag = owner == NR_PROMPT_SOURCE_OWNER_MINIMIZE ? 0x101u :
            owner == NR_PROMPT_SOURCE_OWNER_MAXIMIZE ? 0x102u :
            owner == NR_PROMPT_SOURCE_OWNER_CLOSE ? 0x103u :
            owner == NR_PROMPT_SOURCE_OWNER_RESTORE ? 0x104u :
            owner == NR_PROMPT_SOURCE_OWNER_RESIZE ? 0x105u : 0;
        c->cells[at].id = NR_ID_PROMPT | tag;
    }
    c->characterOwner = previous;
}

void nrPromptFramedPaint(NrContext *c, const State *s) {
    if (!c || !s || !s->promptFramed.enabled) return;
    NrPromptSourceInput input;
    NrPromptSourceLayout layout;
    if (nrPromptFramedLayout(s, &input, &layout) < 0) return;
    PromptSinkContext context = { c, s, &input, layout,
        input.mode == NR_PROMPT_SOURCE_MARQUEE ? (size_t)layout.offset : 0, 0, 0 };
    NrPromptSourceSink sink = { &context, source_background, source_glyph };
    int blend = c->paintBlend;
    c->paintBlend = 0;
    nrPromptSourcePaint(&input, &layout, sink);
    if(input.options.active&&s->promptAppearance.cursorConfigured)nrPromptAppearanceCursor(c,s,layout.caretX,layout.caretY);
    c->paintBlend = blend;
}
