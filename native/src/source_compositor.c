#include "source_compositor.h"

static uint32_t mix(uint32_t a,uint32_t b,int alpha){
    if(alpha>=1000)return b;
    if(alpha<=0)return a;
    uint32_t rgb=0;
    for(int shift=0;shift<24;shift+=8)
        rgb|=((((a>>shift)&255)*(1000-alpha)+((b>>shift)&255)*alpha)/1000)<<shift;
    return rgb;
}
int nrSourceBegin(NrContext*c,int width,int height,int sampling,int orthographic,uint32_t background){
    if(!c||!c->sourceDepth||!c->sourcePickDepth||!c->backgroundPixels||width<=0||height<=0||
       width>c->screenWidth/2||height>c->screenHeight/4||
       (sampling!=0&&sampling!=1)||(orthographic!=0&&orthographic!=1)||background>0xffffff)return 0;
    c->sourceActive=1;c->sourceWidth=width;c->sourceHeight=height;
    c->sourceSampling=sampling;c->sourceOrthographic=orthographic;c->sourceBackground=background;
    memset(c->sourceDepth,0,(size_t)c->screenWidth*c->screenHeight*sizeof(int32_t));
    memset(c->sourcePickDepth,0,(size_t)c->screenWidth*c->screenHeight*sizeof(int32_t));
    for(int y=0;y<height*4;y++)for(int x=0;x<width*2;x++)
        c->backgroundPixels[(size_t)y*c->screenWidth+x]=background;
    return 1;
}
void nrSourcePixel(NrContext*c,int x,int y,int32_t depth,uint32_t rgb,int alpha,int threshold){
    if(!c||!c->sourceActive||x<0||y<0||alpha<=0)return;
    int scale=c->sourceSampling?1:2;
    if(x>=c->sourceWidth*2/scale||y>=c->sourceHeight*4/scale)return;
    for(int j=0;j<scale;j++)for(int i=0;i<scale;i++){
        size_t at=(size_t)(y*scale+j)*c->screenWidth+x*scale+i;
        if(depth<c->sourceDepth[at])continue;
        c->backgroundPixels[at]=mix(c->backgroundPixels[at],rgb,alpha);
        /* Full-alpha source-order paint hides every previous contributor.
         * Translucent paint retains the nearest still-visible surface. */
        if(alpha>=1000||depth>c->sourcePickDepth[at])c->sourcePickDepth[at]=depth;
        if(alpha>=threshold)c->sourceDepth[at]=depth;
    }
}
int nrSourceFragmentVisible(const NrContext*c,int x,int y,double cameraDepth){
    if(!c->sourceActive||x>=c->sourceWidth*2||y>=c->sourceHeight*4)return 1;
    if(x<0||y<0||!(cameraDepth>0))return 0;
    double q=nrFloor(cameraDepth*256+.5);
    if(q<1||q>2147483647.0)return 0;
    int32_t z=(int32_t)q;
    int32_t depth=c->sourceOrthographic?268435456-z:(1<<26)/z;
    return depth>=c->sourceDepth[(size_t)y*c->screenWidth+x];
}
static uint32_t average(const uint32_t*p,unsigned mask){
    unsigned r=0,g=0,b=0,n=0;
    for(int k=0;k<8;k++)if(mask&(1u<<k)){r+=(p[k]>>16)&255;g+=(p[k]>>8)&255;b+=p[k]&255;n++;}
    return n?((r/n)<<16)|((g/n)<<8)|(b/n):0;
}
uint32_t nrResolveSourceSamples(NrCell*out,const uint32_t*p,const int32_t*depths,uint32_t bg,int sampling){
    static const unsigned dots[8]={1,8,2,16,4,32,64,128};
    out->id=0;
    if(!sampling){
        out->foreground=average(p,15);out->background=average(p,240);
        out->glyph=out->foreground==out->background?32:0x2580;
        for(int k=0;k<8;k++)if(depths[k])return 1;
        return 0;
    }
    unsigned occupied=0,mask=0;
    for(int k=0;k<8;k++)if(p[k]!=bg){occupied|=1u<<k;mask|=dots[k];}
    if(!occupied){out->glyph=32;out->foreground=bg;out->background=bg;return 0;}
    /* Explicit braille retains geometry at full occupancy too. Neither a
     * half-block fallback nor bright/dark clustering may paint the dot gaps. */
    out->glyph=0x2800+mask;
    out->foreground=average(p,occupied);
    out->background=bg;
    return 1;
}
