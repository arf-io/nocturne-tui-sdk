#ifndef NR_WINDOW_PALETTE_SOURCE_H
#define NR_WINDOW_PALETTE_SOURCE_H

#include <stdint.h>

#define NR_WINDOW_PALETTE_SOURCE_MAX_STOPS 32u
#define NR_WINDOW_PALETTE_SOURCE_RAMP_SIZE 2048u
#define NR_WINDOW_PALETTE_SOURCE_WHEEL_SIZE 360u

/* Pure RC2 ObservatoryRenderer palette preparation. Colors are packed RGB;
 * weights are the supplied prefix of the original stopWidths option. */
typedef struct {
    uint32_t colorCount;
    uint32_t weightCount;
    uint32_t colors[NR_WINDOW_PALETTE_SOURCE_MAX_STOPS];
    uint32_t backgroundRgb;
    uint32_t inkRgb;
    uint32_t lockLightness;
    uint32_t reserved;
    double weights[NR_WINDOW_PALETTE_SOURCE_MAX_STOPS];
    double lightness;
    double chroma;
    double brightness;
    double hueOffsetDegrees;
    double feather;
    double textLightness;
    double textChroma;
} NrWindowPaletteSourceConfig;

typedef struct {
    uint32_t ramp[NR_WINDOW_PALETTE_SOURCE_RAMP_SIZE];
    uint32_t wheel[NR_WINDOW_PALETTE_SOURCE_WHEEL_SIZE];
    double stopTotal;
} NrWindowPaletteSourcePrepared;

/* Original ObservatoryModel defaults, with stopWidths omitted (unit weights). */
void nrWindowPaletteSourceDefaults(NrWindowPaletteSourceConfig *config);
int nrWindowPaletteSourceValidate(const NrWindowPaletteSourceConfig *config);

/* Returns 0 on success, -1 on invalid input. Failure leaves `prepared`
 * untouched. All arrays are caller-owned; no clock or global state is used. */
int nrWindowPaletteSourcePrepare(const NrWindowPaletteSourceConfig *config,
                                 NrWindowPaletteSourcePrepared *prepared);

/* Match ObservatoryRenderer.colorAt/ink. Lookup phases must be finite and
 * phase/stopTotal and hue must fit the JS safe-integer domain. Failure leaves
 * `rgb` untouched. */
int nrWindowPaletteSourceColorAt(const NrWindowPaletteSourcePrepared *prepared,
                                 double phase, uint32_t *rgb);
int nrWindowPaletteSourceInk(const NrWindowPaletteSourcePrepared *prepared,
                             double hue, uint32_t *rgb);

/* Direct original text hue-wheel sample. Hue rounds to a whole degree before
 * the retained fixed-point converter; authored lightness/chroma remain editable. */
uint32_t nrWindowPaletteSourceFixedOklch(int32_t lightness,int32_t chroma,int32_t hue);
int nrWindowPaletteSourceTextInk(double lightness,double chroma,double hue,uint32_t *rgb);
#endif
