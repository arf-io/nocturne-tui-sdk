#include "internal.h"
static int64_t minimum(int64_t a,int64_t b){return a<b?a:b;}
static int64_t maximum(int64_t a,int64_t b){return a>b?a:b;}
static int64_t clamp(int64_t x,int64_t hi){return x<0?0:x>hi?hi:x;}
int nrResolveArea(const State*s,uint32_t id,int64_t*out){
    const Area*chain[NR_AREAS];int count=0;uint32_t at=id;
    if(!id)return 0;
    while(at){
        if(count>=NR_AREAS)return 0;const Area*found=0;
        for(int i=0;i<NR_AREAS;i++)if(s->areas[i].used&&(uint32_t)s->areas[i].id==at){found=&s->areas[i];break;}
        if(!found)return 0;chain[count++]=found;at=(uint32_t)found->parent;
    }
    int64_t x=0,y=0,left=0,top=0,right=s->width,bottom=s->height;
    for(int i=count-1;i>=0;i--){
        const Area*a=chain[i];x+=a->x;y+=a->y<0?(int64_t)s->height+a->y:a->y;
        left=maximum(left,x);top=maximum(top,y);right=minimum(right,x+a->width);bottom=minimum(bottom,y+a->height);
    }
    const Area*a=chain[0];int64_t pad=a->padding+(a->border?1:0),cx=clamp(left,s->width),cy=clamp(top,s->height),ex=clamp(right,s->width),ey=clamp(bottom,s->height);
    int64_t row[12]={x,y,a->width,a->height,cx,cy,maximum(0,ex-cx),maximum(0,ey-cy),x+pad,y+pad,maximum(0,(int64_t)a->width-2*pad),maximum(0,(int64_t)a->height-2*pad)};
    memcpy(out,row,sizeof(row));return 1;
}
int nrAreaGeometry(const NrContext*c,uint32_t id,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||!id||id>65535||!out||capacity<12||((uintptr_t)out%8)||!nrExternalOutput(c,out,12*sizeof(double)))return -1;
    int64_t geometry[12];if(!nrResolveArea(&c->state,id,geometry))return 0;
    double row[12];for(int i=0;i<12;i++)row[i]=(double)geometry[i];memcpy(out,row,sizeof(row));return 1;
}
