#ifndef NOCTURNE_SOURCE_COMPOSITOR_H
#define NOCTURNE_SOURCE_COMPOSITOR_H
#include "internal.h"

/* Shared render scratch, ordered source pass before native fragments. */
int nrSourceBegin(NrContext*,int width,int height,int sampling,int orthographic,uint32_t background);
void nrSourcePixel(NrContext*,int x,int y,int32_t depth,uint32_t rgb,int alphaPermille,int depthThresholdPermille);
int nrSourceFragmentVisible(const NrContext*,int x,int y,double cameraDepth);
/* Returns original source flags, separately from the RC4 cell hit ID. */
uint32_t nrResolveSourceSamples(NrCell*,const uint32_t pixels[8],const int32_t depths[8],uint32_t background,int sampling);
#endif
