/* Focused real WASM target. Fixed fixture scratch is test-owned, not an SDK cap. */
#include "internal.h"
#include "scenic_native.h"
#include "source_compositor.h"
static NrContext context;
static NrScenicArtConfig config;
static uint32_t pixels[120*40*8],indices[120*40],owners[120*40];
static int32_t depths[120*40*8],pickDepths[120*40*8];
static uint8_t counts[120*40*8];
static uint32_t overflow[120*40*8];
static Fragment fragments[120*40*8][NR_LAYERS];
static NrCell cells[120*40];
static uint32_t records[120*40][4];
int32_t*scenic_config(void){return config.world;}
int32_t*scenic_detail(void){return config.detail;}
uint32_t*scenic_records(void){return records[0];}
int scenic_render(uint32_t timeMs){
    if(config.world[0]!=120||config.world[1]!=40)return -1;
    config.hasWorldDetail=1;
    context.state.width=120;context.state.height=40;context.state.sampling=2;
    context.screenWidth=240;context.screenHeight=160;
    context.cells=cells;context.backgroundPixels=pixels;context.sourceDepth=depths;context.sourcePickDepth=pickDepths;
    context.fragmentCounts=counts;context.fragments=fragments;context.legacyFragmentOverflow=overflow;
    context.characterIndices=indices;context.characterOwners=owners;
    memset(counts,0,sizeof(counts));memset(overflow,0,sizeof(overflow));
    if(!nrSceneArtComposeConfig(&context,&config,timeMs))return -2;
    for(unsigned y=0;y<40;y++)for(unsigned x=0;x<120;x++){
        unsigned at=y*120+x;nrResolveLayerCell(&context,x,y,cells+at);
        uint32_t p[8];int32_t d[8];NrCell reduced;
        for(int k=0;k<8;k++){size_t i=(size_t)(y*4+k/2)*240+x*2+k%2;p[k]=pixels[i];d[k]=depths[i];}
        uint32_t flags=nrResolveSourceSamples(&reduced,p,d,config.world[19],config.world[23]);
        if(memcmp(cells+at,&reduced,sizeof(NrCell)))return -3;
        records[at][0]=cells[at].glyph;records[at][1]=cells[at].foreground;
        records[at][2]=cells[at].background;records[at][3]=flags;
    }
    return 4800;
}
