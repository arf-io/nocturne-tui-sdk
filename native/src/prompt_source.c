#include "prompt_source.h"

#include <float.h>
#include <limits.h>
#include <string.h>

/* Shared native integer OKLCh gamut mapper. The historical Workbench engine
 * calls the same native converter using L/1000, C/10000 and millidegrees. */
extern double nrAbs(double);
extern double nrFloor(double);
extern double nrPowPositive(double,double);
extern double nrSqrt(double);
extern uint32_t nrOklch(int32_t lightness, int32_t chroma, int32_t hue);

enum { PS_MAX_COLOR = 0xffffffu };

typedef struct { int64_t row, col; } SourcePosition;

static int finite_number(double value) {
    return value == value && value <= DBL_MAX && value >= -DBL_MAX;
}

/* Range-reduced alternating series gives a deterministic atan2 angle without
 * importing platform libm into the freestanding WASM build. The transformed
 * series argument is at most sqrt(2)-1, so 40 terms exceed double precision. */
static double atan_small(double value) {
    double reduced = value / (1 + nrSqrt(1 + value * value));
    double squared = reduced * reduced;
    double term = reduced, sum = reduced;
    for (int denominator = 3; denominator <= 81; denominator += 2) {
        term *= -squared;
        sum += term / denominator;
    }
    return 2 * sum;
}

static double atan2_degrees(double y, double x) {
    if (x == 0 && y == 0) return 0;
    double ax = nrAbs(x), ay = nrAbs(y);
    double angle;
    if (ax >= ay) angle = atan_small(ay / ax) * (180.0 / 3.14159265358979323846);
    else angle = 90 - atan_small(ax / ay) * (180.0 / 3.14159265358979323846);
    if (x < 0) angle = 180 - angle;
    return y < 0 ? -angle : angle;
}

static int valid_scalar(uint32_t c) {
    return c <= 0x10ffffu && !(c >= 0xd800u && c <= 0xdfffu);
}

static int valid_options(const NrPromptSourceOptions *o) {
    return o && finite_number(o->alpha) && o->alpha >= 0 && o->alpha <= 1 &&
        o->background <= PS_MAX_COLOR && o->foreground <= PS_MAX_COLOR &&
        o->accent <= PS_MAX_COLOR && o->selectionColor <= PS_MAX_COLOR &&
        o->border >= NR_PROMPT_SOURCE_BORDER_NONE &&
        o->border <= NR_PROMPT_SOURCE_BORDER_HEAVY &&
        o->paddingX >= 0 && o->paddingX <= 8 &&
        o->paddingY >= 0 && o->paddingY <= 4 &&
        o->margin >= 0 && o->margin <= 6 &&
        o->minRows >= 1 && o->minRows <= 24 &&
        o->maxRows >= 1 && o->maxRows <= 60 && o->minRows <= o->maxRows &&
        o->inlineRows >= 5 && o->inlineRows <= 80 &&
        o->inlineWidth >= 24 && o->inlineWidth <= 240 &&
        (o->lineNumbers == 0 || o->lineNumbers == 1) &&
        (o->active == 0 || o->active == 1) &&
        (o->selected == 0 || o->selected == 1) &&
        finite_number(o->hueStep) && o->hueStep >= -360 && o->hueStep <= 360 &&
        finite_number(o->hueSpeed) && o->hueSpeed >= -360 && o->hueSpeed <= 360 &&
        o->huePeriodMs >= 1 && o->huePeriodMs <= 120000 &&
        o->maxChars <= INT32_MAX;
}

static int valid_input(const NrPromptSourceInput *in) {
    if (!in || !valid_options(&in->options) || in->width <= 0 || in->height <= 0 ||
        in->scalarCount > (size_t)INT64_MAX ||
        (in->options.maxChars && in->scalarCount > in->options.maxChars) ||
        (!in->scalars && in->scalarCount) || in->caret > in->scalarCount ||
        in->statusCount > (size_t)INT64_MAX || (!in->statusScalars && in->statusCount) ||
        in->mode < NR_PROMPT_SOURCE_MARQUEE || in->mode > NR_PROMPT_SOURCE_VIM_FULL ||
        in->vimState < NR_PROMPT_SOURCE_VIM_NORMAL || in->vimState > NR_PROMPT_SOURCE_VIM_COMMAND ||
        in->minimizedRestoreMode < 0 || in->minimizedRestoreMode > 2 ||
        (in->hasSelection != 0 && in->hasSelection != 1)) return 0;
    if (in->hasSelection && (in->selectionStart > in->selectionEnd ||
                             in->selectionEnd > in->scalarCount)) return 0;
    for (size_t i = 0; i < in->scalarCount; i++) if (!valid_scalar(in->scalars[i])) return 0;
    for (size_t i = 0; i < in->statusCount; i++) if (!valid_scalar(in->statusScalars[i])) return 0;
    return 1;
}

static int checked_i32(int64_t value, int32_t *out) {
    if (value < INT32_MIN || value > INT32_MAX) return 0;
    *out = (int32_t)value;
    return 1;
}

static int64_t max64(int64_t a, int64_t b) { return a > b ? a : b; }
static int64_t min64(int64_t a, int64_t b) { return a < b ? a : b; }

static int decimal_digits(size_t value) {
    int digits = 1;
    while (value >= 10) { value /= 10; digits++; }
    return digits;
}

/* Match JavaScript String(text).split('\\n').length without allocating. */
static int source_line_count_digits(const NrPromptSourceInput *in) {
    size_t lines = 1;
    for (size_t i = 0; i < in->scalarCount; i++) if (in->scalars[i] == '\n') lines++;
    int digits = decimal_digits(lines) + 1;
    return digits < 3 ? 3 : digits;
}

static int source_wrap(const NrPromptSourceInput *in, int64_t width,
                       int64_t *rowCount, SourcePosition *caret) {
    int64_t row = 0, col = 0;
    SourcePosition at = {0, 0};
    int caretFound = 0;
    if (in->caret == 0) { at.row = 0; at.col = 0; caretFound = 1; }
    for (size_t i = 0; i < in->scalarCount; i++) {
        if (col == width) { row++; col = 0; }
        if (i == in->caret) { at.row = row; at.col = col; caretFound = 1; }
        if (in->scalars[i] == '\n') { row++; col = 0; }
        else col++;
    }
    if (col == width) { row++; col = 0; }
    if (in->caret == in->scalarCount) { at.row = row; at.col = col; caretFound = 1; }
    if (!caretFound || row == INT64_MAX) return 0;
    *rowCount = row + 1;
    *caret = at;
    return 1;
}

static int layout_values(const NrPromptSourceInput *in, NrPromptSourceLayout *out) {
    const NrPromptSourceOptions *o = &in->options;
    int vim = in->mode >= NR_PROMPT_SOURCE_VIM_INLINE;
    int full = in->mode == NR_PROMPT_SOURCE_VIM_FULL;
    int64_t margin = min64(o->margin, in->width > 12 ? (in->width - 12) / 2 : 0);
    int64_t border = o->border != NR_PROMPT_SOURCE_BORDER_NONE || vim ? 1 : 0;
    int64_t width = full || !vim ? in->width - 2 * margin :
        min64(in->width - 2 * margin, o->inlineWidth);
    int64_t numberWidth = vim && o->lineNumbers ? source_line_count_digits(in) : 0;
    int64_t prefix = vim ? 0 : 2;
    int64_t innerWidth = max64(1, width - 2 * border - 2 * o->paddingX - numberWidth - prefix);
    int64_t wrappedRows = 0;
    SourcePosition caret = {0, 0};
    if (!source_wrap(in, innerWidth, &wrappedRows, &caret)) return 0;

    int64_t maxAvail = max64(1, in->height - 9 - 2 * border - 2 * o->paddingY - (vim ? 1 : 0));
    int64_t visibleRows;
    if (in->mode == NR_PROMPT_SOURCE_MARQUEE) visibleRows = 1;
    else if (in->mode == NR_PROMPT_SOURCE_GROW)
        visibleRows = max64(min64(o->minRows, maxAvail),
                            min64(wrappedRows, min64(o->maxRows, maxAvail)));
    else if (full) visibleRows = max64(1, in->height - 8 - 2 * o->paddingY);
    else visibleRows = min64(maxAvail,
        max64(1, o->inlineRows - 2 * border - 2 * o->paddingY - 1));
    visibleRows = max64(1, visibleRows);

    int64_t height = visibleRows + 2 * border + 2 * o->paddingY + (vim ? 1 : 0);
    int64_t x = full || !vim ? margin : (in->width - width) / 2;
    int64_t y = in->height - 2 - height;
    int64_t innerX = x + border + o->paddingX + numberWidth + prefix;
    int64_t innerY = y + border + o->paddingY;
    int64_t offset = 0, top = 0, caretX = innerX, caretY = innerY;
    if (in->mode == NR_PROMPT_SOURCE_MARQUEE) {
        offset = max64(0, (int64_t)in->caret - innerWidth + 1);
        caretX = innerX + (int64_t)in->caret - offset;
    } else {
        top = max64(0, caret.row - visibleRows + 1);
        caretX = innerX + caret.col;
        caretY = innerY + caret.row - top;
    }
    int64_t extraRows = full ? 0 : max64(0, height - 1);
    int64_t sceneHeight = max64(12, in->height - extraRows);

    memset(out, 0, sizeof(*out));
    if (!checked_i32(x, &out->rectX) || !checked_i32(y, &out->rectY) ||
        !checked_i32(width, &out->rectWidth) || !checked_i32(height, &out->rectHeight) ||
        !checked_i32(innerX, &out->innerX) || !checked_i32(innerY, &out->innerY) ||
        !checked_i32(innerWidth, &out->innerWidth) || !checked_i32(visibleRows, &out->innerHeight) ||
        !checked_i32(caretX, &out->caretX) || !checked_i32(caretY, &out->caretY) ||
        !checked_i32(visibleRows, &out->visibleRows) || !checked_i32(border, &out->border) ||
        !checked_i32(numberWidth, &out->numberWidth) || !checked_i32(prefix, &out->prefix) ||
        !checked_i32(top, &out->top) || !checked_i32(offset, &out->offset) ||
        !checked_i32(extraRows, &out->extraRows) || !checked_i32(sceneHeight, &out->sceneHeight)) return 0;
    out->full = full;
    out->vim = vim;
    return 1;
}

int nrPromptSourceLayout(const NrPromptSourceInput *in, NrPromptSourceLayout *out) {
    if (!out || !valid_input(in)) return -1;
    NrPromptSourceLayout candidate;
    if (!layout_values(in, &candidate)) return -1;
    *out = candidate;
    return 0;
}

static int inside(const NrPromptSourceInput *in, int64_t x, int64_t y) {
    return x >= 0 && y >= 0 && x < in->width && y < in->height &&
        x >= INT32_MIN && x <= INT32_MAX && y >= INT32_MIN && y <= INT32_MAX;
}

static void emit_glyph(const NrPromptSourceInput *in, NrPromptSourceSink sink,
                       int64_t x, int64_t y, uint32_t cp, uint32_t color,
                       int kind, int owner) {
    if (inside(in, x, y)) sink.glyph(sink.context, (int32_t)x, (int32_t)y,
                                    cp, color, 1.0, kind, owner);
}

static void emit_background(const NrPromptSourceInput *in, NrPromptSourceSink sink,
                            int64_t x, int64_t y, uint32_t color, double alpha,
                            int kind, int owner) {
    if (inside(in, x, y)) sink.background(sink.context, (int32_t)x, (int32_t)y,
                                        color, alpha, kind, owner);
}

static int decorative(uint32_t cp) {
    return cp == 32 || cp == 0x2580 || cp == 0x2584 || cp == 0x258c || cp == 0x2590 ||
        (cp >= 0x2800 && cp <= 0x28ff);
}

static const uint32_t *border_glyphs(int border) {
    static const uint32_t glyphs[5][6] = {
        {' ', ' ', ' ', ' ', ' ', ' '},
        {0x256d, 0x256e, 0x2570, 0x256f, 0x2500, 0x2502},
        {0x250c, 0x2510, 0x2514, 0x2518, 0x2500, 0x2502},
        {0x2554, 0x2557, 0x255a, 0x255d, 0x2550, 0x2551},
        {0x250f, 0x2513, 0x2517, 0x251b, 0x2501, 0x2503}
    };
    return glyphs[border];
}

static void write_text(const NrPromptSourceInput *in, const NrPromptSourceLayout *l,
                       NrPromptSourceSink sink, int64_t x, int64_t y,
                       const uint32_t *text, size_t count, uint32_t color,
                       int kind, int owner) {
    for (size_t i = 0; i < count; i++, x++) {
        if (x >= (int64_t)l->rectX + l->rectWidth - 1) break;
        emit_glyph(in, sink, x, y, text[i], color, kind, owner);
    }
}

static size_t ascii(const char *text, uint32_t *out, size_t cap) {
    size_t n = 0;
    while (text[n] && n < cap) { out[n] = (unsigned char)text[n]; n++; }
    return n;
}

static void write_literal(const NrPromptSourceInput *in, const NrPromptSourceLayout *l,
                          NrPromptSourceSink sink, int64_t x, int64_t y,
                          const char *text, uint32_t color, int kind, int owner) {
    uint32_t chars[96];
    size_t count = ascii(text, chars, sizeof(chars) / sizeof(chars[0]));
    write_text(in, l, sink, x, y, chars, count, color, kind, owner);
}

static int source_color(uint32_t rgb, int64_t index, const NrPromptSourceOptions *o,
                        uint64_t timeMs, uint32_t *color) {
    if (o->hueStep == 0 && o->hueSpeed == 0) { *color = rgb; return 1; }
    double r = (double)((rgb >> 16) & 255) / 255.0;
    double g = (double)((rgb >> 8) & 255) / 255.0;
    double b = (double)(rgb & 255) / 255.0;
    r = r <= .04045 ? r / 12.92 : nrPowPositive((r + .055) / 1.055, 2.4);
    g = g <= .04045 ? g / 12.92 : nrPowPositive((g + .055) / 1.055, 2.4);
    b = b <= .04045 ? b / 12.92 : nrPowPositive((b + .055) / 1.055, 2.4);
    double l = nrPowPositive(.4122214708 * r + .5363325363 * g + .0514459929 * b, 1.0 / 3.0);
    double m = nrPowPositive(.2119034982 * r + .6806995451 * g + .1073969566 * b, 1.0 / 3.0);
    double s = nrPowPositive(.0883024619 * r + .2817188376 * g + .6299787005 * b, 1.0 / 3.0);
    double L = .2104542553 * l + .793617785 * m - .0040720468 * s;
    double a = 1.9779984951 * l - 2.428592205 * m + .4505937099 * s;
    double bb = .0259040371 * l + .7827717662 * m - .808675766 * s;
    double C = nrSqrt(a * a + bb * bb);
    double H = atan2_degrees(bb, a);
    if (H < 0) H += 360.0;
    double hue = H + (double)index * o->hueStep +
        ((double)timeMs / (double)o->huePeriodMs) * o->hueSpeed;
    double hueMilli = hue * 1000.0;
    if (!finite_number(hueMilli) || hueMilli < INT32_MIN || hueMilli > INT32_MAX) return 0;
    int64_t lightness = (int64_t)nrFloor(L * 1000.0 + .5) * 1000;
    int64_t chroma = (int64_t)nrFloor(C * 10000.0 + .5) * 100;
    int64_t roundedHue = (int64_t)nrFloor(hueMilli + .5);
    if (lightness < 0 || lightness > 1000000 || chroma < 0 || chroma > 400000 ||
        roundedHue < INT32_MIN || roundedHue > INT32_MAX) return 0;
    *color = nrOklch((int32_t)lightness, (int32_t)chroma, (int32_t)roundedHue);
    return *color <= PS_MAX_COLOR;
}

static int preflight_colors(const NrPromptSourceInput *in, const NrPromptSourceLayout *l) {
    const NrPromptSourceOptions *o = &in->options;
    if (!o->hueStep && !o->hueSpeed) return 1;
    int64_t last = in->mode == NR_PROMPT_SOURCE_MARQUEE ?
        min64((int64_t)in->scalarCount, l->offset + l->innerWidth) : (int64_t)in->scalarCount;
    int64_t row=0,col=0;
    for(int64_t i=0;i<last;i++){
        if(in->mode!=NR_PROMPT_SOURCE_MARQUEE){
            if(col==l->innerWidth){row++;col=0;}
            if(in->scalars[i]=='\n'){row++;col=0;continue;}
            if(row<l->top||row>=(int64_t)l->top+l->visibleRows){col++;continue;}
        } else if(i<l->offset) continue;
        uint32_t color;
        if (!source_color(o->foreground, i, o, in->timeMs, &color)) return 0;
        if(in->mode!=NR_PROMPT_SOURCE_MARQUEE)col++;
    }
    return 1;
}

static void draw_frame(const NrPromptSourceInput *in, const NrPromptSourceLayout *l,
                       NrPromptSourceSink sink) {
    const uint32_t *bg = border_glyphs(in->options.border);
    const uint32_t *g = bg;
    int vim = l->vim;
    if (vim && in->options.border == NR_PROMPT_SOURCE_BORDER_NONE) g = border_glyphs(NR_PROMPT_SOURCE_BORDER_ROUNDED);
    if (l->border) {
        for (int64_t x = l->rectX + 1; x < (int64_t)l->rectX + l->rectWidth - 1; x++) {
            emit_glyph(in, sink, x, l->rectY, g[4], in->options.accent,
                       NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
            emit_glyph(in, sink, x, (int64_t)l->rectY + l->rectHeight - 1, g[4], in->options.accent,
                       NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
        }
        for (int64_t y = l->rectY + 1; y < (int64_t)l->rectY + l->rectHeight - 1; y++) {
            emit_glyph(in, sink, l->rectX, y, g[5], in->options.accent,
                       NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
            emit_glyph(in, sink, (int64_t)l->rectX + l->rectWidth - 1, y, g[5], in->options.accent,
                       NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
        }
        emit_glyph(in, sink, l->rectX, l->rectY, g[0], in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
        emit_glyph(in, sink, (int64_t)l->rectX + l->rectWidth - 1, l->rectY, g[1], in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
        emit_glyph(in, sink, l->rectX, (int64_t)l->rectY + l->rectHeight - 1, g[2], in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
        emit_glyph(in, sink, (int64_t)l->rectX + l->rectWidth - 1,
                   (int64_t)l->rectY + l->rectHeight - 1, g[3], in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_CHROME, NR_PROMPT_SOURCE_OWNER_BODY);
    }

    if (vim) {
        static const uint32_t stateNames[][8] = {
            {'N','O','R','M','A','L',0}, {'I','N','S','E','R','T',0},
            {'V','I','S','U','A','L',0}, {'C','O','M','M','A','N','D',0}
        };
        static const char *titlePrefix = " VIM MODE " "\xc2\xb7 ";
        /* UTF-8 literals are expanded explicitly to source scalar cells. */
        uint32_t title[32]; size_t n=0;
        const char *p=titlePrefix;
        while (*p && n < 24) {
            unsigned char c=(unsigned char)*p++;
            if(c<0x80) title[n++]=c;
            else if((c&0xe0)==0xc0){title[n++]=((uint32_t)(c&31)<<6)|((uint32_t)((unsigned char)*p++&63));}
            else if((c&0xf0)==0xe0){unsigned char c2=(unsigned char)*p++,c3=(unsigned char)*p++;title[n++]=((uint32_t)(c&15)<<12)|((uint32_t)(c2&63)<<6)|(uint32_t)(c3&63);}
        }
        for (size_t i=0; i<8 && stateNames[in->vimState][i]; i++) title[n++]=stateNames[in->vimState][i];
        title[n++]=' ';
        n=(size_t)min64((int64_t)n,max64(0,(int64_t)l->rectWidth-21));
        write_text(in,l,sink,(int64_t)l->rectX+2,l->rectY,title,n,in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_CHROME,NR_PROMPT_SOURCE_OWNER_BODY);
        int64_t bx=(int64_t)l->rectX+l->rectWidth-17;
        write_literal(in,l,sink,bx,l->rectY,"[ - ]",0xdcc17e,
                      NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_MINIMIZE);
        if (l->full)
            write_literal(in,l,sink,bx+5,l->rectY,"[ ",0x8ccfc4,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_MAXIMIZE),
            emit_glyph(in,sink,bx+7,l->rectY,0x25c7,0x8ccfc4,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_MAXIMIZE),
            write_literal(in,l,sink,bx+8,l->rectY," ]",0x8ccfc4,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_MAXIMIZE);
        else
            write_literal(in,l,sink,bx+5,l->rectY,"[ ",0x8ccfc4,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_MAXIMIZE),
            emit_glyph(in,sink,bx+7,l->rectY,0x25a1,0x8ccfc4,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_MAXIMIZE),
            write_literal(in,l,sink,bx+8,l->rectY," ]",0x8ccfc4,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_MAXIMIZE);
        write_literal(in,l,sink,bx+10,l->rectY,"[ ",0xe2a4ad,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_CLOSE);
        emit_glyph(in,sink,bx+12,l->rectY,0x00d7,0xe2a4ad,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_CLOSE);
        write_literal(in,l,sink,bx+13,l->rectY," ]",0xe2a4ad,NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_CLOSE);
        write_text(in,l,sink,(int64_t)l->rectX+2,(int64_t)l->rectY+l->rectHeight-2,
                   in->statusScalars,in->statusCount,in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_CHROME,NR_PROMPT_SOURCE_OWNER_BODY);
        emit_glyph(in,sink,(int64_t)l->rectX+l->rectWidth-3,
                   (int64_t)l->rectY+l->rectHeight-1,0x2198,in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_RESIZE);
        emit_glyph(in,sink,(int64_t)l->rectX+l->rectWidth-2,
                   (int64_t)l->rectY+l->rectHeight-1,' ',in->options.accent,
                   NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_RESIZE);
    } else if (in->minimizedRestoreMode) {
        write_literal(in,l,sink,(int64_t)l->rectX+2,l->rectY,"[ VIM restore ]",in->options.accent,
                      NR_PROMPT_SOURCE_PAINT_ACTION,NR_PROMPT_SOURCE_OWNER_RESTORE);
    } else if (l->border) {
        if (in->mode == NR_PROMPT_SOURCE_GROW)
            write_literal(in,l,sink,(int64_t)l->rectX+2,l->rectY," GROWING PROMPT ",in->options.accent,
                          NR_PROMPT_SOURCE_PAINT_CHROME,NR_PROMPT_SOURCE_OWNER_BODY);
        else
            write_literal(in,l,sink,(int64_t)l->rectX+2,l->rectY," SCROLLING PROMPT ",in->options.accent,
                          NR_PROMPT_SOURCE_PAINT_CHROME,NR_PROMPT_SOURCE_OWNER_BODY);
    }
}

static void draw_body(const NrPromptSourceInput *in, const NrPromptSourceLayout *l,
                      NrPromptSourceSink sink) {
    const NrPromptSourceOptions *o=&in->options;
    int64_t firstIndex=-1, firstX=0, firstY=0;
    int64_t wrappedRows=1;
    SourcePosition ignored;
    source_wrap(in,l->innerWidth,&wrappedRows,&ignored);
    if (in->mode == NR_PROMPT_SOURCE_MARQUEE) {
        int64_t end=min64((int64_t)in->scalarCount,(int64_t)l->offset+l->innerWidth);
        for (int64_t i=l->offset;i<end;i++) {
            uint32_t cp=in->scalars[i];
            if (cp=='\n') cp=0x21b5;
            int64_t x=(int64_t)l->innerX+i-l->offset,y=l->innerY;
            if (i==(int64_t)in->caret){firstIndex=i;firstX=x;firstY=y;}
            if (cp<0x20||cp==0x7f) cp=' ';
            if (in->hasSelection && (size_t)i>=in->selectionStart && (size_t)i<in->selectionEnd)
                emit_background(in,sink,x,y,o->selectionColor,.8,NR_PROMPT_SOURCE_PAINT_SELECTION,NR_PROMPT_SOURCE_OWNER_BODY);
            uint32_t color;
            if (source_color(o->foreground,i,o,in->timeMs,&color))
                emit_glyph(in,sink,x,y,cp,color,NR_PROMPT_SOURCE_PAINT_AUTHORED,NR_PROMPT_SOURCE_OWNER_BODY);
        }
    } else {
        int64_t row=0,col=0;
        int64_t visibleEnd=(int64_t)l->top+l->visibleRows;
        int64_t rowAtCaret=0,colAtCaret=0;
        int caretFound=0;
        if(in->caret==0){rowAtCaret=0;colAtCaret=0;caretFound=1;}
        for(size_t i=0;i<in->scalarCount;i++){
            if(col==l->innerWidth){row++;col=0;}
            if(i==in->caret){rowAtCaret=row;colAtCaret=col;caretFound=1;}
            uint32_t cp=in->scalars[i];
            if(cp=='\n'){
                row++;col=0;
                continue;
            }
            if(row>=l->top && row<visibleEnd){
                int64_t x=(int64_t)l->innerX+col,y=(int64_t)l->innerY+row-l->top;
                if(i==in->caret){firstIndex=(int64_t)i;firstX=x;firstY=y;}
                if(i< (size_t)INT64_MAX && in->hasSelection && i>=in->selectionStart && i<in->selectionEnd)
                    emit_background(in,sink,x,y,o->selectionColor,.8,NR_PROMPT_SOURCE_PAINT_SELECTION,NR_PROMPT_SOURCE_OWNER_BODY);
                uint32_t color;
                if(cp<0x20||cp==0x7f)cp=' ';
                if(source_color(o->foreground,(int64_t)i,o,in->timeMs,&color))
                    emit_glyph(in,sink,x,y,cp,color,NR_PROMPT_SOURCE_PAINT_AUTHORED,NR_PROMPT_SOURCE_OWNER_BODY);
            }
            col++;
        }
        if(col==l->innerWidth){row++;col=0;}
        if(in->caret==in->scalarCount){rowAtCaret=row;colAtCaret=col;caretFound=1;}
        if(caretFound && rowAtCaret>=l->top && rowAtCaret<visibleEnd){
            firstX=(int64_t)l->innerX+colAtCaret;
            firstY=(int64_t)l->innerY+rowAtCaret-l->top;
            firstIndex=(int64_t)in->caret;
        }
    }
    int64_t drawnRows=in->mode==NR_PROMPT_SOURCE_MARQUEE?1:
        min64(l->visibleRows,max64(0,wrappedRows-l->top));
    for(int64_t row=0;row<drawnRows;row++){
        int64_t y=(int64_t)l->innerY+row;
        if(l->numberWidth){
            int64_t value=(int64_t)l->top+row+1;
            uint32_t digits[32];size_t n=0;
            char reversed[32];size_t count=0;
            do{reversed[count++]=(char)('0'+value%10);value/=10;}while(value&&count<sizeof(reversed));
            while(count<(size_t)l->numberWidth-1)reversed[count++]=' ';
            while(count)digits[n++]=(uint32_t)reversed[--count];
            digits[n++]=' ';
            write_text(in,l,sink,(int64_t)l->innerX-l->numberWidth,y,digits,n,0x83929e,
                       NR_PROMPT_SOURCE_PAINT_CHROME,NR_PROMPT_SOURCE_OWNER_BODY);
        }
        if(l->prefix && row==0){
            static const uint32_t prefix[]={'>',' '};
            write_text(in,l,sink,(int64_t)l->innerX-2,y,prefix,2,o->accent,
                       NR_PROMPT_SOURCE_PAINT_CHROME,NR_PROMPT_SOURCE_OWNER_BODY);
        }
    }
    if(o->active && inside(in,l->caretX,l->caretY)){
        uint32_t existing=' ';
        if(firstIndex>=0 && firstX==l->caretX && firstY==l->caretY && firstIndex<(int64_t)in->scalarCount){
            existing=in->scalars[firstIndex];
            if(in->mode==NR_PROMPT_SOURCE_MARQUEE && existing=='\n') existing=0x21b5;
            if(existing=='\n'||existing==0x85||existing==0x2028||existing==0x2029||existing<0x20||existing==0x7f)existing=' ';
        }
        if(decorative(existing))
            emit_glyph(in,sink,l->caretX,l->caretY,0x258f,o->accent,
                       NR_PROMPT_SOURCE_PAINT_CURSOR,NR_PROMPT_SOURCE_OWNER_BODY);
        else
            emit_background(in,sink,l->caretX,l->caretY,o->accent,.18,
                            NR_PROMPT_SOURCE_PAINT_CURSOR,NR_PROMPT_SOURCE_OWNER_BODY);
    }
}

int nrPromptSourcePaint(const NrPromptSourceInput *in, const NrPromptSourceLayout *layout,
                        NrPromptSourceSink sink) {
    if (!valid_input(in) || !layout || !sink.background || !sink.glyph) return -1;
    NrPromptSourceLayout expected;
    if (!layout_values(in,&expected) || memcmp(layout,&expected,sizeof(expected)) ||
        !preflight_colors(in,layout)) return -1;
    for(int64_t y=layout->rectY;y<(int64_t)layout->rectY+layout->rectHeight;y++)
        for(int64_t x=layout->rectX;x<(int64_t)layout->rectX+layout->rectWidth;x++)
            emit_background(in,sink,x,y,in->options.background,in->options.alpha,
                            NR_PROMPT_SOURCE_PAINT_PANEL,NR_PROMPT_SOURCE_OWNER_BODY);
    draw_frame(in,layout,sink);
    draw_body(in,layout,sink);
    return 0;
}
