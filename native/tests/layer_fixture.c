/* Test-only construction of exact coverage; never linked into production builds. */
#include "internal.h"
#include <stdlib.h>
int layerProbe(unsigned mask,double alpha,int front,int sampling,int duplicates,NrCell *out) {
    NrContext *c=calloc(1,sizeof(*c));if(!c)return -1;
    nrInit(c,sizeof(*c),42);c->state.width=c->state.height=1;
    c->screenWidth=2;c->screenHeight=4;
    static const unsigned dots[8]={1,8,2,16,4,32,64,128};
    for(int i=0;i<8;i++){
        c->backgroundPixels[i]=0x101018;
        c->paintOwner=1;c->paintDetail=0;c->paintSampling=1;
        nrPixel(c,i%2,i/2,front?4:20,0x263a51,alpha);
        if(mask&dots[i]){
            c->paintOwner=2;c->paintDetail=1;c->paintSampling=sampling;
            for(int k=0;k<duplicates;k++)nrPixel(c,i%2,i/2,10,0xe5ab61,.8);
        }
    }
    nrResolveLayerCell(c,0,0,out);free(c);return 0;
}
int lineDepthProbe(void) {
    NrContext*c=calloc(1,sizeof(*c));if(!c)return -1;
    nrInit(c,sizeof(*c),1);c->screenWidth=40;c->screenHeight=4;
    c->paintOwner=1;c->paintDetail=1;c->paintSampling=2;
    Projection p={.right={1,0,0},.up={0,1,0},.forward={0,0,-1},.cx=20,.cy=2,.focal=20,.nearPlane=.1,.farPlane=100};
    nrLine(c,&p,nrV(-5,0,-5),nrV(20,0,-20),0xffffff,1);
    int depth=c->fragments[2*40+20][0].depth;free(c);return depth;
}
int opaqueBackdropProbe(void) {
    NrContext*c=calloc(1,sizeof(*c));if(!c)return -1;
    nrInit(c,sizeof(*c),1);c->clip=(ClipRect){0,0,1,1};
    c->cells[0]=(NrCell){0x2588,0xabcdef,0x123456,0};
    nrGlyph(c,0,0,'X',0xffffff,1,12);
    int result=c->cells[0].background;free(c);return result;
}
