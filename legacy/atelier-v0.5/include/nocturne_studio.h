/* Additive Studio ABI. v1 layout/behavior is preserved. */
#ifndef NOCTURNE_STUDIO_H
#define NOCTURNE_STUDIO_H
#include "nocturne.h"
#ifdef __cplusplus
extern "C" {
#endif
#define NST_ABI_VERSION 2
#define NST_MAX_EVENTS 128
#define NST_MAX_NODES 512
#define NST_MAX_TEXT 32768
#define NST_MAX_DATA 16384
typedef struct { int32_t values[64]; uint32_t palette[32], starPalette[32], glyphs[32], novaGlyphs[16]; } NsStageConfig;
/* xQ8,yQ8,strength,kind,timeLow,timeHigh,id,reserved. Time words are unsigned bits. */
typedef struct { int32_t values[8]; } NsImpulse;
/* Flat scene record, indexed by enum NsNodeKey. Array order is z order. */
typedef struct { int32_t values[32]; } NsNode;
enum NsStageKey {
 NST_WIDTH = 0,
 NST_HEIGHT = 1,
 NST_PATTERN = 2,
 NST_FOCUS_MODE = 3,
 NST_FOCUS_X = 4,
 NST_FOCUS_Y = 5,
 NST_PERIOD_MS = 6,
 NST_SATURATION = 7,
 NST_BRIGHTNESS = 8,
 NST_SPEED_FALLOFF = 9,
 NST_SATURATION_FALLOFF = 10,
 NST_BRIGHTNESS_FALLOFF = 11,
 NST_CELL_ASPECT = 12,
 NST_SCALE = 13,
 NST_ANGLE = 14,
 NST_PIVOT_X = 15,
 NST_PIVOT_Y = 16,
 NST_ROTATION_PERIOD_MS = 17,
 NST_ROTATION_MODE = 18,
 NST_SWING = 19,
 NST_PHASE = 20,
 NST_PIXEL_MODE = 21,
 NST_SEED = 22,
 NST_BASE_COLOR = 23,
 NST_INK_COLOR = 24,
 NST_PALETTE_COUNT = 25,
 NST_GRADIENT_WRAP = 26,
 NST_INTERPOLATION = 27,
 NST_COLOR_MODE = 28,
 NST_HUE_OFFSET = 29,
 NST_STARS = 30,
 NST_STAR_DENSITY = 31,
 NST_STAR_MIN_MS = 32,
 NST_STAR_RANGE_MS = 33,
 NST_STAR_DUTY = 34,
 NST_STAR_PEAK = 35,
 NST_STAR_GLYPH_COUNT = 36,
 NST_STAR_COLOR_COUNT = 37,
 NST_NOVA_CHANCE = 38,
 NST_NOVA_CYCLE_MS = 39,
 NST_NOVA_DURATION_MS = 40,
 NST_NOVA_GLYPH_COUNT = 41,
 NST_RIPPLE_SPEED = 42,
 NST_RIPPLE_WIDTH = 43,
 NST_RIPPLE_LIFE_MS = 44,
 NST_RIPPLE_OPACITY = 45,
 NST_RIPPLE_RINGS = 46,
 NST_MOTION = 47,
 NST_QUANTIZE = 48,
 NST_ORIGIN_X = 49,
 NST_ORIGIN_Y = 50,
 NST_WAVE_AMPLITUDE = 51,
 NST_STAR_ATTACK = 52,
 NST_REVERSE = 53
};
enum NsNodeKey {
 NTN_KIND = 0,
 NTN_ID = 1,
 NTN_X = 2,
 NTN_Y = 3,
 NTN_WIDTH = 4,
 NTN_HEIGHT = 5,
 NTN_STATE = 6,
 NTN_VALUE = 7,
 NTN_FROM_VALUE = 8,
 NTN_CHANGED_LO = 9,
 NTN_CHANGED_HI = 10,
 NTN_DURATION_MS = 11,
 NTN_FG = 12,
 NTN_BG = 13,
 NTN_FG_OPACITY = 14,
 NTN_BG_OPACITY = 15,
 NTN_STYLE = 16,
 NTN_TEXT_OFFSET = 17,
 NTN_TEXT_LENGTH = 18,
 NTN_DATA_OFFSET = 19,
 NTN_DATA_LENGTH = 20,
 NTN_HUE_STEP = 21,
 NTN_HUE_SPEED = 22,
 NTN_HUE_BASE = 23,
 NTN_REVEAL_MS = 24,
 NTN_RESERVED = 25,
 NTN_HUE_SATURATION = 26,
 NTN_HUE_BRIGHTNESS = 27,
 NTN_COLOR_ANIMATION = 28,
 NTN_GLYPH = 29,
 NTN_ZOOM = 30,
 NTN_RESERVED2 = 31
};
enum NsNodeKind {
 NTK_TEXT = 0,
 NTK_BOX = 1,
 NTK_RULE = 2,
 NTK_BUTTON = 3,
 NTK_ITEM = 4,
 NTK_CURSOR = 5,
 NTK_PROGRESS = 6,
 NTK_BARS = 7,
 NTK_PIE = 8,
 NTK_DONUT = 9,
 NTK_SCATTER = 10,
 NTK_LINE = 11,
 NTK_DIGITS = 12,
 NTK_EDGE = 13
};
/** Initialize all bytes; no allocation or host side effects. */
NS_API void nsStageDefaults(NsStageConfig *config);
/** Validate entire configuration. 0 success; positive one-based key or array error. */
NS_API int32_t nsStageValidate(const NsStageConfig *config);
/** Pure rendering. Returns cell count or negative error. No partially rendered output
 * on validation errors. Input pointers must be live, aligned, nonoverlapping buffers.
 * -1 config; -2 cells/capacity; -3 event input; -4 scene input.
 * Empty dimensions are valid. Arrays may be NULL only when count is zero.
 * Examples and units: docs/STUDIO_API.md and studio.schema.json. */
NS_API int32_t nsStageRender(const NsStageConfig *config,uint64_t timeMs,
 const NsImpulse *events,uint32_t eventCount,const NsNode *nodes,uint32_t nodeCount,
 const uint32_t *text,uint32_t textCount,const int32_t *data,uint32_t dataCount,
 NsCell *cells,uint32_t capacity);
/** Hit-test reverse z order. Returns ((nodeIndex+1)<<16)|(itemIndex+1), 0 no hit,
 * or -1 invalid inputs. Disabled interactive nodes block hits underneath them.
 * Charts use geometric segment / nearest-point picking. */
NS_API int32_t nsStageHit(const NsNode *nodes,uint32_t nodeCount,const int32_t *data,
 uint32_t dataCount,int32_t x,int32_t y);
/** Composite source-over cells, no terminal alpha escapes. glyph=0 means no ink.
 * Text over a half-block background flattens its two colors. Supports negative
 * offsets and clipping. Returns 0 success, -1 invalid input. */
NS_API int32_t nsStageComposite(NsCell *dest,int32_t dw,int32_t dh,const NsCell *src,
 int32_t sw,int32_t sh,int32_t x,int32_t y,int32_t fgOpacity,int32_t bgOpacity);
/** Pure scalar keyframe interpolation: 0 linear, 1 smoothstep, 2 sine ease,
 * 3 cubic ease-out. Clamped before/after interval. Duration zero commits target. */
NS_API int32_t nsStageTween(int32_t from,int32_t to,uint64_t elapsedMs,uint32_t durationMs,int32_t easing);
NS_API uint32_t nsStageVersion(void);
NS_API uint32_t nsStageConfigSize(void);
/* Additive Fleet visual function. All opacity values are thousandths.
 * ageMs/fadeMs: arrival age/duration; fadeMs=0 means immediately visible.
 * rowQ8: distance from transcript top in cells*256; bandQ8=0 disables horizon.
 * topMinimum: 0..1000; returns 0..1000 or -1 for invalid band/minimum.
 * Pure, integer arithmetic; does not modify text, events or terminal state. */
NS_API int32_t nsFleetInkOpacity(uint32_t ageMs,uint32_t fadeMs,int32_t rowQ8,int32_t bandQ8,int32_t topMinimum);
/** OKLCh to sRGB. L: 0..1000, C: 0..4000 (=0..0.4), h: signed millidegrees.
 * Returns packed RGB or -1 invalid. Chroma reduces to gamut at fixed L/h.
 * Pure Q20 integer math, shared across native and WASM. */
NS_API int32_t nsOklchColor(int32_t lightness,int32_t chroma,int32_t hueMilliDegrees);
/** Approximate Oklab L, 0..1000, for packed sRGB; -1 for invalid RGB. */
NS_API int32_t nsOklchLightness(uint32_t color);
/** Paint validated scene nodes directly over an owned existing frame. No clear,
 * no background generation. Same bounds/errors as nsStageRender; -4 scene invalid.
 * All input validation precedes mutation. capacity is measured in cells. */
NS_API int32_t nsStagePaint(const NsStageConfig *config,uint64_t timeMs,
 const NsNode *nodes,uint32_t nodeCount,const uint32_t *text,uint32_t textCount,
 const int32_t *data,uint32_t dataCount,NsCell *cells,uint32_t capacity);
#ifdef __cplusplus
}
#endif
#endif
