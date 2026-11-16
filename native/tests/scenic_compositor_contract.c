/* Test the actual shared sample storage/resolver, not a replacement canvas. */
#include "internal.h"
#include "scenic_native.h"
#include "source_compositor.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static NrContext *context(int w,int h) {
    NrContext *c=calloc(1,sizeof(*c)); assert(c);
    c->state.width=w;c->state.height=h;c->state.sampling=2;
    c->screenWidth=w*2;c->screenHeight=h*4;
    size_t cells=(size_t)w*h,samples=cells*8;
    c->cells=calloc(cells,sizeof(*c->cells));
    c->backgroundPixels=calloc(samples,sizeof(uint32_t));
    c->sourceDepth=calloc(samples,sizeof(int32_t));
    c->sourcePickDepth=calloc(samples,sizeof(int32_t));
    c->fragmentCounts=calloc(samples,1);
    c->legacyFragmentOverflow=calloc(samples,sizeof(uint32_t));
    c->fragments=calloc(samples,sizeof(*c->fragments));
    c->characterIndices=calloc(cells,sizeof(uint32_t));
    c->characterOwners=calloc(cells,sizeof(uint32_t));
    assert(c->cells&&c->backgroundPixels&&c->sourceDepth&&c->sourcePickDepth&&c->fragments&&c->fragmentCounts&&c->legacyFragmentOverflow&&c->characterIndices&&c->characterOwners);
    return c;
}
static void destroy(NrContext*c){free(c->cells);free(c->backgroundPixels);free(c->sourceDepth);free(c->sourcePickDepth);free(c->fragments);free(c->fragmentCounts);free(c->legacyFragmentOverflow);free(c->characterIndices);free(c->characterOwners);free(c);}
static void begin(NrContext*c,int sampling){assert(nrSourceBegin(c,c->state.width,c->state.height,sampling,1,0x102030));}
static void thresholds(void){
    NrContext*c=context(2,2);
    for(int threshold=750;threshold<=950;threshold+=200)for(int a=threshold-1;a<=threshold+1;a++){
        begin(c,1);nrSourcePixel(c,0,0,100,0xffffff,a,threshold);
        assert(c->sourceDepth[0]==(a>=threshold?100:0));
        uint32_t prior=c->backgroundPixels[0];nrSourcePixel(c,0,0,99,0,1000,750);
        assert(c->backgroundPixels[0]==(a>=threshold?prior:0));
    }
    begin(c,1);nrSourcePixel(c,0,0,100,0xff0000,500,750);nrSourcePixel(c,0,0,100,0x0000ff,500,750);
    assert(c->backgroundPixels[0]==0x43088b);assert(c->sourceDepth[0]==0);
    nrSourcePixel(c,0,0,100,0x00ff00,500,750);nrSourcePixel(c,0,0,100,0xffffff,500,750);
    assert(c->backgroundPixels[0]==0x90c1a2);assert(c->fragmentOverflow==0);
    uint32_t unchanged=c->backgroundPixels[0];
    nrSourcePixel(c,-1,0,100,0,1000,750);nrSourcePixel(c,0,8,100,0,1000,750);
    assert(c->backgroundPixels[0]==unchanged);
    begin(c,1);assert(c->sourcePickDepth[0]==0);
    nrSourcePixel(c,0,0,100,0xff0000,500,950);
    assert(c->sourceDepth[0]==0&&c->sourcePickDepth[0]==100);
    nrSourcePixel(c,0,0,99,0x0000ff,1000,950);
    assert(c->sourceDepth[0]==99&&c->sourcePickDepth[0]==99&&c->backgroundPixels[0]==0x0000ff);
    nrSourcePixel(c,0,0,101,0xffffff,500,950);
    assert(c->sourceDepth[0]==99&&c->sourcePickDepth[0]==101);
    nrSourcePixel(c,0,0,98,0,1000,950);
    assert(c->sourceDepth[0]==99&&c->sourcePickDepth[0]==101);
    nrSourcePixel(c,0,0,100,0x123456,1000,950);
    assert(c->sourceDepth[0]==100&&c->sourcePickDepth[0]==100&&c->backgroundPixels[0]==0x123456);
    nrSourcePixel(c,0,0,102,0,0,950);assert(c->sourcePickDepth[0]==100);
    assert(!nrSourceBegin(c,3,2,1,1,0));assert(!nrSourceBegin(c,2,2,2,1,0));
    begin(c,0);nrSourcePixel(c,0,0,100,0xabcdef,1000,750);
    for(int y=0;y<2;y++)for(int x=0;x<2;x++)assert(c->backgroundPixels[y*4+x]==0xabcdef);
    assert(c->backgroundPixels[2]==0x102030);assert(c->backgroundPixels[8]==0x102030);
    destroy(c);
}
static void mixed(void){
    NrContext*c=context(1,1);begin(c,1);
    const int32_t sourceZ=268435456-10*256;
    for(int y=0;y<4;y++)for(int x=0;x<2;x++)nrSourcePixel(c,x,y,sourceZ,0x336699,1000,750);
    c->paintOwner=2;c->paintSampling=2;
    nrPixel(c,0,0,11,0xffffff,1);assert(c->fragmentCounts[0]==0);
    nrPixel(c,0,0,9,0xffffff,1);assert(c->fragmentCounts[0]==1);
    NrCell out;nrResolveLayerCell(c,0,0,&out);
    assert(out.glyph==0x2801&&out.foreground==0xffffff&&out.background==0x336699&&out.id==0);
    memset(c->fragmentCounts,0,8);begin(c,1);
    nrSourcePixel(c,0,0,sourceZ,0xff0000,749,750);
    nrPixel(c,0,0,11,0xffffff,1);assert(c->fragmentCounts[0]==1); /* intentional no depth write */
    memset(c->fragmentCounts,0,8);c->sourceActive=0;
    for(int k=0;k<8;k++)c->backgroundPixels[k]=0x102030;
    for(int y=0;y<4;y++)for(int x=0;x<2;x++)nrPixel(c,x,y,9,0xaabbcc,1);
    nrResolveLayerCell(c,0,0,&out);assert(out.glyph==0x28ff&&out.foreground==0xaabbcc&&out.background==0x102030);
    destroy(c);
}
static void mixed_geometry(void){
    NrContext*c=context(8,4);begin(c,1);
    for(int y=0;y<16;y++)for(int x=0;x<16;x++)nrSourcePixel(c,x,y,268435456-2560,0x336699,1000,750);
    Projection p={.position={0,0,0},.right={1,0,0},.up={0,1,0},.forward={0,0,1},
        .focal=8,.cx=8,.cy=8,.orthographic=1,.nearPlane=1.5,.farPlane=100,.scale=1};
    c->paintOwner=2;c->paintSampling=2;
    nrTriangle(c,&p,(Triangle){{-4,-4,11},{4,-4,11},{0,4,11},0xff0000,1});
    for(int k=0;k<256;k++)assert(c->fragmentCounts[k]==0);
    nrTriangle(c,&p,(Triangle){{-4,-4,9},{4,-4,9},{0,4,9},0xff0000,1});
    assert(c->fragmentCounts[8*16+8]);
    memset(c->fragmentCounts,0,256);c->paintOwner=0x10000001;c->paintDetail=1;
    nrPoint(c,&p,(Vec3){0,0,11},0xffffff,1,1);
    for(int k=0;k<256;k++)assert(c->fragmentCounts[k]==0);
    nrPoint(c,&p,(Vec3){0,0,9},0xffffff,1,1);
    assert(c->fragmentCounts[8*16+8]);
    destroy(c);
}
static void reduction(void){
    uint32_t pixels[8]={0},bg=0x112233;int32_t depths[8]={0};NrCell out;
    for(int k=0;k<8;k++)pixels[k]=bg;
    assert(nrResolveSourceSamples(&out,pixels,depths,bg,1)==0);
    assert(out.glyph==32&&out.foreground==bg&&out.background==bg&&out.id==0);
    pixels[0]=0xffffff;assert(nrResolveSourceSamples(&out,pixels,depths,bg,1)==1);
    assert(out.glyph==0x2801&&out.foreground==0xffffff&&out.background==bg);
    for(int k=0;k<8;k++)pixels[k]=k<4?0x203040:0x304050;
    nrResolveSourceSamples(&out,pixels,depths,bg,1);assert(out.glyph==0x28ff&&out.foreground==0x283848&&out.background==bg);
    for(int k=0;k<8;k++)pixels[k]=k%2?0xffffff:0;
    nrResolveSourceSamples(&out,pixels,depths,bg,1);assert(out.glyph==0x28ff&&out.foreground==0x7f7f7f&&out.background==bg);
    for(int k=0;k<8;k++)pixels[k]=0x123456;
    assert(nrResolveSourceSamples(&out,pixels,depths,bg,0)==0);assert(out.glyph==32);
    depths[0]=1;assert(nrResolveSourceSamples(&out,pixels,depths,bg,0)==1);
}
static void invalid_frame(void){
    NrContext*c=context(120,40);NrScenicArtConfig q={0};
    const int32_t world[24]={120,40,0,-17408,12288,-24576,8960,-5632,0,15872,1,37120,1000,0,2030,700,3072,1,940,1053726,0,0,0,1};
    memcpy(q.world,world,sizeof(world));
    const int32_t detail[8]={358,8704,5632,480,430,620,1000,1};
    memcpy(q.detail,detail,sizeof(detail));assert(nrScenicArtValidate(&q));
    c->backgroundPixels[0]=0x123456;
    assert(!nrSceneArtComposeConfig(c,&q,UINT64_C(9007199254740992)));
    assert(!c->sourceActive&&c->backgroundPixels[0]==0x123456);
    q.world[2]=5;assert(!nrSceneArtComposeConfig(c,&q,0));
    assert(!c->sourceActive&&c->backgroundPixels[0]==0x123456);
    destroy(c);
}
static void projection_bridge(void){
    NrContext*c=context(120,40);State*s=&c->state;s->schema=NR_STATE_SCHEMA;
    const int32_t world[24]={120,40,0,-17408,12288,-24576,8960,-5632,0,15872,1,37120,1000,0,2030,700,3072,1,940,1053726,0,0,0,1};
    const int32_t detail[8]={358,8704,5632,480,430,620,1000,1};
    s->sceneArt.used=1;s->sceneArt.hasWorldDetail=1;
    memcpy(s->sceneArt.world,world,sizeof(world));memcpy(s->sceneArt.detail,detail,sizeof(detail));
    s->camera=(Camera){.position={0,0,0},.fov=90,.nearPlane=.1,.farPlane=1000,.span=120};
    Projection p;nrProjection(s,120,40,&p);double x,y,z;
    assert(p.sourceEnabled);assert(nrProject(&p,(Vec3){2,1,-10},&x,&y,&z));
    assert(x==144&&y==68&&z==10); /* original +Z becomes canonical -Z */
    assert(!nrProject(&p,(Vec3){2,1,10},&x,&y,&z));
    s->camera.orthographic=1;nrProjection(s,120,40,&p);
    assert(nrProject(&p,(Vec3){2,1,-10},&x,&y,&z));assert(x==124&&y==78&&z==10);
    s->sceneArt.world[23]=0;nrProjection(s,120,40,&p);
    assert(nrProject(&p,(Vec3){2,1,-10},&x,&y,&z));assert(x==124&&y==78&&z==10);
    s->sceneArt.used=0;s->camera.orthographic=0;nrProjection(s,120,40,&p);
    assert(!p.sourceEnabled);assert(nrProject(&p,(Vec3){2,1,-10},&x,&y,&z));
    assert(nrAbs(x-136)<.000001&&nrAbs(y-72)<.000001&&z==10); /* existing vertical optics */
    destroy(c);
}
static int frame(const char*table,const char*directory){
    FILE*f=fopen(table,"r");assert(f);char name[128];unsigned long long time;
    while(fscanf(f,"%127s %llu",name,&time)==2){
        NrScenicArtConfig q={0};q.hasWorldDetail=1;
        for(int i=0;i<24;i++)assert(fscanf(f,"%d",q.world+i)==1);
        for(int i=0;i<8;i++)assert(fscanf(f,"%d",q.detail+i)==1);
        NrContext*c=context(q.world[0],q.world[1]);
        assert(nrSceneArtComposeConfig(c,&q,time));
        char path[1024];snprintf(path,sizeof(path),"%s/%s.cells",directory,name);FILE*out=fopen(path,"wb");assert(out);
        for(unsigned y=0;y<c->state.height;y++)for(unsigned x=0;x<c->state.width;x++){
            NrCell cell;nrResolveLayerCell(c,x,y,&cell);assert(cell.id==0);
            uint32_t pixels[8];int32_t depths[8];
            for(int k=0;k<8;k++){size_t at=(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2;pixels[k]=c->backgroundPixels[at];depths[k]=c->sourceDepth[at];}
            NrCell reduced;uint32_t flags=nrResolveSourceSamples(&reduced,pixels,depths,q.world[19],q.world[23]);
            assert(!memcmp(&cell,&reduced,sizeof(cell)));
            uint32_t record[]={cell.glyph,cell.foreground,cell.background,flags};assert(fwrite(record,sizeof(record),1,out)==1);
        }
        fclose(out);destroy(c);
    }fclose(f);return 0;
}
int main(int argc,char**argv){thresholds();mixed();mixed_geometry();reduction();invalid_frame();projection_bridge();if(argc==3)return frame(argv[1],argv[2]);puts("source order, thresholds, mixed depth, no-scene braille and cell reduction pass");return 0;}
