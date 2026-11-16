/* Generated configuration indices. Regenerate with scripts/create_schema.py. */
#ifndef NOCTURNE_H
#define NOCTURNE_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define NS_ABI_VERSION 1
#define NS_MAX_WIDTH 512
#define NS_MAX_HEIGHT 256
#define NS_MAX_CELLS (NS_MAX_WIDTH * NS_MAX_HEIGHT)
#define NS_MAX_TEXT 512
#if defined(_WIN32)
#define NS_API __declspec(dllexport)
#else
#define NS_API __attribute__((visibility("default")))
#endif
typedef struct { uint32_t glyph, fg, bg, flags; } NsCell;
typedef struct {
    int32_t values[64];
    uint32_t palette[8];
    uint32_t starPalette[8];
    uint32_t glyphs[32];
} NsConfig;
enum NsKey {
    NS_WIDTH = 0,
    NS_HEIGHT = 1,
    NS_EFFECT = 2,
    NS_LAYOUT = 3,
    NS_SEED = 4,
    NS_STARS = 5,
    NS_DENSITY_PERMILLE = 6,
    NS_GLYPH_SET = 7,
    NS_STAR_PERIOD_MIN_MS = 8,
    NS_STAR_PERIOD_RANGE_MS = 9,
    NS_STAR_DUTY_PERMILLE = 10,
    NS_STAR_FLOOR_PERMILLE = 11,
    NS_STAR_PEAK_PERMILLE = 12,
    NS_GRADIENT_PERIOD_MS = 13,
    NS_SATURATION_PERMILLE = 14,
    NS_BRIGHTNESS_PERMILLE = 15,
    NS_FOCUS_ROW = 16,
    NS_NEIGHBOR_SPEED_PERMILLE = 17,
    NS_NEIGHBOR_SATURATION_PERMILLE = 18,
    NS_NEIGHBOR_BRIGHTNESS_PERMILLE = 19,
    NS_ANGLE_DEGREES = 20,
    NS_SCALE_CELLS = 21,
    NS_HUE_STEP_DEGREES = 22,
    NS_HUE_DEGREES_PER_SECOND = 23,
    NS_BASE_HUE_DEGREES = 24,
    NS_PIXEL_MODE = 25,
    NS_ORIGIN_X = 26,
    NS_ORIGIN_Y = 27,
    NS_VALUE_PERMILLE = 28,
    NS_MOTION = 29,
    NS_PHASE_DEGREES = 30,
    NS_GRAIN_PERMILLE = 31,
    NS_CURSOR_MODE = 32,
    NS_BORDER_STYLE = 33,
    NS_SELECTION = 34,
    NS_FOREGROUND_COLOR = 35,
    NS_BASE_COLOR = 36,
    NS_WAVE_AMPLITUDE_PERMILLE = 37,
    NS_STAR_ATTACK_PERMILLE = 38,
    NS_PALETTE_COUNT = 39,
    NS_STAR_PALETTE_COUNT = 40,
    NS_GLYPH_COUNT = 41,
    NS_MODAL_OPEN = 42,
    NS_HUE_SATURATION_PERMILLE = 43,
    NS_HUE_BRIGHTNESS_PERMILLE = 44,
    NS_CELL_ASPECT_PERMILLE = 45,
    NS_TEXT_SCRIM_PERMILLE = 46,
    NS_PROMPT_BANDS = 47,
    NS_COLOR_MODE = 48
};
/** Initialize every configuration byte. No allocation and no terminal I/O. */
NS_API void nsDefaultConfig(NsConfig *config);
/** Return zero for valid config, otherwise the one-based invalid key index. */
NS_API int32_t nsValidateConfig(const NsConfig *config);
/** Render caller-owned cells. Returns count, or -1 invalid config, -2 buffer,
 * -3 invalid text length/pointer. Text is a bounded code-point array; unsupported
 * or unsafe glyphs become '?'. No state, wall clock, allocation, or terminal I/O.
 * Example: nsRender(&config, 1000, NULL, 0, cells, width*height).
 * Pointers must reference suitably aligned, live, non-overlapping buffers. */
NS_API int32_t nsRender(const NsConfig *config, uint64_t motionMs,
    const uint32_t *text, uint32_t textLength, NsCell *cells, uint32_t capacity);
/** Exact effective row period in ms after distance falloff; config must be valid. */
NS_API uint64_t nsRowPeriod(const NsConfig *config, uint32_t distance);
/** Exact effective row saturation after distance falloff; config must be valid. */
NS_API int32_t nsRowSaturation(const NsConfig *config, uint32_t distance);
NS_API uint32_t nsAbiVersion(void);
NS_API uint32_t nsConfigSize(void);
NS_API uint32_t nsCellSize(void);
#ifdef __cplusplus
}
#endif
#endif
