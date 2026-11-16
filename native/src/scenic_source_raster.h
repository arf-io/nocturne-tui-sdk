#ifndef NOCTURNE_SCENIC_SOURCE_RASTER_H
#define NOCTURNE_SCENIC_SOURCE_RASTER_H

#include "scenic_art.h"
#include <stdint.h>

/* One callback per geometrically covered source sample. `sampleX/Y` use the
 * original renderer's internal raster dimensions; the shared compositor owns
 * depth testing, blending, and mapping into its common sample accumulator. */
typedef void (*NrScenicSourceCoverageSink)(void *user,
    int32_t sampleX,int32_t sampleY,int32_t sourceDepth,uint32_t rgb,
    int32_t alphaPermille,int32_t depthThresholdPermille);

typedef struct {
    NrScenicArtConfig config; /* owned copy; never points at caller stack */
    int32_t outputWidth,outputHeight;
    int32_t sampleWidth,sampleHeight;
    int32_t sinYaw,cosYaw,sinPitch,cosPitch,sinRoll,cosRoll,focal;
    int32_t orthographic;
    void *coverageUser;
    NrScenicSourceCoverageSink coverage;
    NrScenicArtSink primitives;
} NrScenicSourceRaster;

/* outputWidth/Height are the canonical scene viewport. RC2 source raster
 * dimensions are width*(sampling?2:1), height*(sampling?4:2). */
int nrScenicSourceRasterInit(NrScenicSourceRaster *raster,
    const NrScenicArtConfig *config,int32_t outputWidth,int32_t outputHeight,
    NrScenicSourceCoverageSink coverage,void *coverageUser);
const NrScenicArtSink *nrScenicSourceRasterSink(NrScenicSourceRaster *raster);

/* Fixed-point source projection witness for shared native geometry. Input and
 * returned camera XYZ are Q8; screen XY are source 1/16-pixel coordinates.
 * Returns zero for invalid args or points behind the original z=384 plane. */
int nrScenicSourceRasterProjectPoint(const NrScenicSourceRaster *raster,
    int32_t worldX,int32_t worldY,int32_t worldZ,
    int32_t *cameraX,int32_t *cameraY,int32_t *cameraZ,
    int32_t *screenX16,int32_t *screenY16,int32_t *sourceDepth);

#endif
