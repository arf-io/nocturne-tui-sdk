#include "internal.h"
/* Dot order follows the physical 2-column by 4-row grid. U+28FF stays braille,
 * never U+2588. Coverage is geometry, not a brightness classifier. */
static const unsigned DOTS[8]={1,8,2,16,4,32,64,128};
static uint32_t average(const uint32_t *values,unsigned mask) {
    unsigned r=0,g=0,b=0,n=0;
    for(int i=0;i<8;i++)if(mask&DOTS[i]){uint32_t v=values[i];r+=(v>>16)&255;g+=(v>>8)&255;b+=v&255;n++;}
    if(!n)return 0;
    return ((r+n/2)/n)<<16|((g+n/2)/n)<<8|(b+n/2)/n;
}
/* Pure current-contract encoder. pixels are already composited; background is
 * the surface before geometric fragments. Alpha must not be applied twice.
 * Geometric coverage under hybrid is a braille object (MIXED-LAYERS.md, Hybrid
 * dictation): the exact U+2800+mask, U+28FF included, never a contrast substitute.
 * Only an uncovered cell, which no object owns, reaches the environment reducer. */
void nrResolveSamples(NrCell *cell,const uint32_t *pixels,const uint32_t *background,unsigned coverage,int sampling) {
    cell->glyph=32;cell->foreground=0xcdd9d1;cell->background=average(pixels,255);cell->id=0;
    if(sampling==1){cell->glyph=0x2580;cell->foreground=average(pixels,27);cell->background=average(pixels,228);return;}
    if((sampling==2||sampling==3)&&coverage){
        cell->glyph=0x2800+(coverage&255);cell->foreground=average(pixels,coverage&255);
        cell->background=average(background,255);return;
    }
    if(sampling<2)return;
    double lum[8],mean=0,variance=0;unsigned dots=0;
    for(int i=0;i<8;i++){lum[i]=((pixels[i]>>16)&255)*.3+((pixels[i]>>8)&255)*.59+(pixels[i]&255)*.11;mean+=lum[i]/8;}
    for(int i=0;i<8;i++){variance+=nrAbs(lum[i]-mean);if(lum[i]>mean+1)dots|=DOTS[i];}
    if(variance>12&&dots&&dots!=255){cell->glyph=0x2800+dots;cell->foreground=average(pixels,dots);cell->background=average(pixels,255^dots);}
    else if(sampling==3){cell->glyph=0x2580;cell->foreground=average(pixels,27);cell->background=average(pixels,228);}
}
