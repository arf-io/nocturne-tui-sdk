#ifndef NOCTURNE_SCENIC_ART_H
#define NOCTURNE_SCENIC_ART_H

#include <stdint.h>

/* Source identities are the original rc2 WorldEngine scene indexes. */
typedef enum {
    NR_SCENIC_PEARL_CASCADE = 0,       /* waterfall */
    NR_SCENIC_COPPER_CAUSEWAY = 1,     /* tarmac */
    NR_SCENIC_RED_SHIFT = 2,           /* black-hole */
    NR_SCENIC_TIDAL_GLASS = 3,         /* ocean */
    NR_SCENIC_SILT = 4                 /* dunes */
} NrScenicArtId;

/* Indices mirror the exact rc2 WORLD_FIELDS descriptor (24 signed Q values).
 * This deliberately carries all fields so retained root State can pass the
 * original vector losslessly. Presentation-only entries remain root-owned. */
enum {
    NR_WORLD_WIDTH = 0, NR_WORLD_HEIGHT = 1, NR_WORLD_SCENE = 2,
    NR_WORLD_CAMERA_X = 3, NR_WORLD_CAMERA_Y = 4, NR_WORLD_CAMERA_Z = 5,
    NR_WORLD_YAW = 6, NR_WORLD_PITCH = 7, NR_WORLD_ROLL = 8,
    NR_WORLD_FOV = 9, NR_WORLD_PROJECTION = 10, NR_WORLD_SPAN = 11,
    NR_WORLD_FLOW = 12, NR_WORLD_TRAVEL = 13, NR_WORLD_SEED = 14,
    NR_WORLD_REDSHIFT = 15, NR_WORLD_DISC_TILT = 16, NR_WORLD_DETAIL = 17,
    NR_WORLD_WATER_ALPHA = 18, NR_WORLD_BACKGROUND = 19, NR_WORLD_INK = 20,
    NR_WORLD_ACCENT = 21, NR_WORLD_SECONDARY = 22, NR_WORLD_SAMPLING = 23,
    NR_WORLD_FIELD_COUNT = 24
};

/* Exact rc2 WORLD_DETAIL_FIELDS order. Units/scales/ranges are documented in
 * native/docs/TDD-original-scenic-art-20261013.md. */
enum {
    NR_WORLD_DETAIL_WAVE_HEIGHT = 0, NR_WORLD_DETAIL_WAVELENGTH = 1,
    NR_WORLD_DETAIL_WIND_ANGLE = 2, NR_WORLD_DETAIL_CROSS_SWELL = 3,
    NR_WORLD_DETAIL_CHOPPINESS = 4, NR_WORLD_DETAIL_FOAM = 5,
    NR_WORLD_DETAIL_WAVE_SPEED = 6, NR_WORLD_DETAIL_JOIN_RIVER = 7,
    NR_WORLD_DETAIL_FIELD_COUNT = 8
};

typedef struct {
    int32_t world[NR_WORLD_FIELD_COUNT];
    int32_t detail[NR_WORLD_DETAIL_FIELD_COUNT];
    uint8_t hasWorldDetail;
} NrScenicArtConfig;

/* All positions are signed Q8 (world units * 256), matching the rc2 geometry
 * source. Color is 0xRRGGBB; alpha is 0..1000 permille. Point radius retains
 * rc2 wDot's screen-sample units (not world units). */
typedef struct {
    void *user;
    void (*triangle)(void *user,
                     int32_t ax, int32_t ay, int32_t az,
                     int32_t bx, int32_t by, int32_t bz,
                     int32_t cx, int32_t cy, int32_t cz,
                     uint32_t rgb, int32_t alphaPermille);
    void (*line)(void *user,
                 int32_t ax, int32_t ay, int32_t az,
                 int32_t bx, int32_t by, int32_t bz,
                 uint32_t rgb, int32_t alphaPermille);
    void (*point)(void *user, int32_t x, int32_t y, int32_t z,
                  uint32_t rgb, int32_t alphaPermille, int32_t sampleRadius);
} NrScenicArtSink;

/* Pure, source-faithful world-geometry sampler. `timeMs` is the original rc2
 * absolute millisecond clock (the unified public clock is converted by root).
 * `nrScenicArtValidate` enforces exact original authoring domains. Effective
 * render views use the explicit wider camera envelope in
 * `nrScenicArtValidateView`; all non-camera source values remain strictly
 * descriptor-validated. */
int nrScenicArtValidate(const NrScenicArtConfig *config);
int nrScenicArtValidateView(const NrScenicArtConfig *config);
int nrScenicArtDraw(const NrScenicArtConfig *config, uint64_t timeMs,
                    const NrScenicArtSink *sink);

#endif
