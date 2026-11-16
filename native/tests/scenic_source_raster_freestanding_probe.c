#include "scenic_source_raster.h"
#include "../../src/world_fields.inc"
#include "../../src/world_detail_fields.inc"

static uint32_t coverageCount;
static void coverage(void *user,int32_t x,int32_t y,int32_t depth,uint32_t rgb,
                     int32_t alpha,int32_t threshold) {
    (void)user;(void)x;(void)y;(void)depth;(void)rgb;(void)alpha;(void)threshold;
    coverageCount++;
}

int scenic_source_raster_freestanding_probe(void) {
    NrScenicArtConfig config={0};
    for(int i=0;i<NR_WORLD_FIELD_COUNT;i++)config.world[i]=WORLD_DEFAULT[i];
    for(int i=0;i<NR_WORLD_DETAIL_FIELD_COUNT;i++)config.detail[i]=WDETAIL_DEFAULT[i];
    config.hasWorldDetail=1;
    config.world[NR_WORLD_CAMERA_X]=0;config.world[NR_WORLD_CAMERA_Y]=0;config.world[NR_WORLD_CAMERA_Z]=0;
    config.world[NR_WORLD_YAW]=0;config.world[NR_WORLD_PITCH]=0;config.world[NR_WORLD_ROLL]=0;
    config.world[NR_WORLD_PROJECTION]=0;
    NrScenicSourceRaster raster;
    if(!nrScenicSourceRasterInit(&raster,&config,120,40,coverage,0))return 1;
    if(raster.sampleWidth!=240||raster.sampleHeight!=160||raster.focal<=0)return 2;
    const NrScenicArtSink *sink=nrScenicSourceRasterSink(&raster);if(!sink)return 3;
    sink->triangle(sink->user,-5*256,-5*256,20*256,5*256,-5*256,20*256,
                   0,5*256,20*256,0x62b8a7,1000);
    sink->line(sink->user,-10*256,0,20*256,10*256,0,20*256,0xe2dfd0,1000);
    sink->point(sink->user,0,0,20*256,0xffffff,1000,0);
    if(coverageCount==0)return 4;
    int32_t cx=0,cy=0,cz=0,sx=0,sy=0,depth=0;
    if(!nrScenicSourceRasterProjectPoint(&raster,0,0,20*256,&cx,&cy,&cz,&sx,&sy,&depth))return 5;
    if(cx||cy||cz!=20*256||sx!=raster.sampleWidth*8||sy!=raster.sampleHeight*8||depth!=(1<<26)/(20*256))return 6;
    if(nrScenicSourceRasterProjectPoint(&raster,0,0,-2*256,&cx,&cy,&cz,&sx,&sy,&depth))return 7;
    NrScenicSourceRaster beyondLegacySourceUi;
    if(!nrScenicSourceRasterInit(&beyondLegacySourceUi,&config,600,257,coverage,0)||
       beyondLegacySourceUi.sampleWidth!=1200||beyondLegacySourceUi.sampleHeight!=1028)return 8;
    return 0;
}
