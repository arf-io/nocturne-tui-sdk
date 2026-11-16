#include "scenic_native.h"
#include "scenic_source_raster.h"
#include "source_compositor.h"

static void sample(void *user,int32_t x,int32_t y,int32_t depth,uint32_t rgb,
                   int32_t alpha,int32_t threshold){
    nrSourcePixel(user,x,y,depth,rgb,alpha,threshold);
}
int nrSceneArtComposeConfig(NrContext*c,const NrScenicArtConfig*q,uint64_t timeMs){
    NrScenicSourceRaster raster;
    if(!c||!q||timeMs>UINT64_C(9007199254740991)||!nrScenicSourceRasterInit(&raster,q,q->world[0],q->world[1],sample,c))return 0;
    if(!nrSourceBegin(c,q->world[0],q->world[1],q->world[NR_WORLD_SAMPLING],
                      q->world[NR_WORLD_PROJECTION],q->world[NR_WORLD_BACKGROUND]))return 0;
    return nrScenicArtDraw(q,timeMs,nrScenicSourceRasterSink(&raster));
}
int nrSceneArtDrawSource(NrContext*c,const Projection*p,const State*s,int width,int height,uint32_t owner){
    (void)p;(void)owner; /* Source flags and interactive hit IDs have distinct contracts. */
    if(!c||!s)return 0;
    if(!s->sceneArt.used)return 1;
    NrScenicArtConfig q;
    if(!nrSceneArtEffective(s,width,height,&q))return 0;
    return nrSceneArtComposeConfig(c,&q,s->sceneArtClock.enabled?(uint64_t)s->sceneArtClock.timeMs:s->timeUs/1000);
}
