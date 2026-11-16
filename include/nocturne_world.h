#ifndef NOCTURNE_WORLD_H
#define NOCTURNE_WORLD_H
#include "nocturne.h"
/* World API v1. All geometry uses Q8 world coordinates and Q8 angles.
 * Native callers own output and scratch. Two scratch elements per cell for sampling=0; eight for sampling=1.
 * No clock, I/O, global mutable state, allocation, or host callbacks. */
#define NSW_CONFIG_WORDS 24
#define NSW_SCENES 5
#define NSW_MAX_WIDTH 512
#define NSW_MAX_HEIGHT 256
#ifdef __cplusplus
extern "C" {
#endif
typedef struct NsWorldConfig { int32_t v[NSW_CONFIG_WORDS]; } NsWorldConfig;
enum NsWorldField {
 NSW_WIDTH,NSW_HEIGHT,NSW_SCENE,NSW_CAMERA_X,NSW_CAMERA_Y,NSW_CAMERA_Z,
 NSW_YAW,NSW_PITCH,NSW_ROLL,NSW_FOV,NSW_PROJECTION,NSW_SPAN,
 NSW_FLOW,NSW_TRAVEL,NSW_SEED,NSW_REDSHIFT,NSW_DISC_TILT,NSW_DETAIL,
 NSW_WATER_ALPHA,NSW_BACKGROUND,NSW_INK,NSW_ACCENT,NSW_SECONDARY,NSW_SAMPLING
};
NS_API uint32_t nsWorldVersion(void);
NS_API uint32_t nsWorldConfigSize(void);
NS_API void nsWorldDefaults(NsWorldConfig *config);
/* Returns cells written, or -1 for invalid input/capacity. On validation error
 * no output is modified. flags=1 identifies geometry coverage, not a hit ID. */
NS_API int32_t nsWorldRender(const NsWorldConfig *config,uint64_t timeMs,
 NsCell *out,uint32_t capacity,uint32_t *colors,int32_t *depth,uint32_t scratchCapacity);
/* Additive v0.9 extension: eight fixed-order fields; see world-detail.schema.json.
 * Coordinates use Q8, opacity/speed thousandths, time explicit milliseconds.
 * Legacy nsWorldRender is unchanged. No callbacks, allocation, or retained pointers. */
#define NSW_DETAIL_WORDS 8
#define NSW_MAX_TRIANGLES 16000
#define NSW_MESH_LIMIT 8388608

typedef struct NsWorldDetail { int32_t v[NSW_DETAIL_WORDS]; } NsWorldDetail;
typedef struct NsWorldTriangle { int32_t vertices[9]; uint32_t color; } NsWorldTriangle;
NS_API uint32_t nsWorldExtensionVersion(void);
NS_API void nsWorldDetailDefaults(NsWorldDetail *detail);
NS_API int32_t nsWorldRenderDetailed(const NsWorldConfig *config,uint64_t timeMs,
 const NsWorldDetail *detail,NsCell *out,uint32_t capacity,uint32_t *colors,
 int32_t *depth,uint32_t scratchCapacity);
NS_API int32_t nsWorldRenderMesh(const NsWorldConfig *config,uint64_t timeMs,
 const NsWorldTriangle *triangles,uint32_t triangleCount,NsCell *out,
 uint32_t capacity,uint32_t *colors,int32_t *depth,uint32_t scratchCapacity);
#ifdef __cplusplus
}
#endif
#endif
