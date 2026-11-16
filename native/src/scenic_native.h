#ifndef NOCTURNE_SCENIC_NATIVE_H
#define NOCTURNE_SCENIC_NATIVE_H

#include "internal.h"
#include "scenic_art.h"

/* Public dispatch remains root-owned; this helper mutates only the supplied
 * transaction State after validating the complete command. */
int nrSceneArtCommand(NrContext *, State *, const Json *);
int nrValidSceneArt(const State *);

/* Copy the lossless authored vector, then map canonical Camera values into the
 * effective source camera fields. `width` and `height` validate/pin the
 * compositor viewport without rewriting retained authoring; explicit scene-art
 * width/height options update the authored dimensions. */
int nrSceneArtEffective(const State *, int width, int height,
                        NrScenicArtConfig *out);

/* Source-Q8 raster into shared sample storage, preserving original projection,
 * coverage order, alpha and depth writes. Public scene dispatch is a separate
 * integration gate; this helper alone does not configure application chrome. */
int nrSceneArtDrawSource(NrContext *, const Projection *, const State *,
                         int sceneWidth, int sceneHeight, uint32_t sceneOwner);
/* Ordered raster into common sample storage; no completed-cell overlay. */
int nrSceneArtComposeConfig(NrContext *,const NrScenicArtConfig *,uint64_t timeMs);

/* Exact fixed-point bridge used by all three ordered primitive callbacks. */
Vec3 nrSceneArtQ8ToVec3(int32_t xQ8, int32_t yQ8, int32_t zQ8);
/* Source-specific natural-to-Q conversion (ECMAScript Math.round ties). */
int nrSceneArtQFromNatural(double value, double min, double max, int scale,
                           int integral, int32_t *out);
/* RC2 0=half sampling, 1=2x4 braille sampling; RC4 modes are 1 and 2. */
int nrSceneArtSamplingMode(int sourceSampling);

#endif
