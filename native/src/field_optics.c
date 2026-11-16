#include "internal.h"
/* Current native optical primitives derived from retained source references.
 * No historical renderer, runtime, clock or host calls are linked here. */
static uint32_t silkColor(const Field*f,const FieldControls*q,double distance){
    static const uint32_t palette[]={0x28304f,0x785c89,0x367876,0xae7357,0x504565};
    double phase=(f->seed%1024)/1024.0+distance/48*q->frequency/100+q->phase/360;
    phase-=nrFloor(phase);phase*=5;int a=(int)phase;double p=phase-a;p=p*p*(3-2*p);
    return nrMix(palette[a],palette[(a+1)%5],p);
}
void nrSourceFieldCurve(const State*s,int i,double distance,uint32_t*color,double*intensity){
    const Field*f=&s->fields[i];const FieldControls*q=&s->fieldControls[i];uint32_t profile=NR_FIELD_OPTICS(q);
    double age=(s->timeUs-f->atUs)/1e6,radius=q->continuous?0:2*age*f->speed,band=2*f->width;
    double fade=q->continuous?1:nrClamp(1-age/(f->lifeUs/1e6),0,1),alpha=1,value=0;
    if(profile==1){
        uint32_t count=NR_FIELD_RINGS(q);if(!count)count=2;
        for(uint32_t k=0;k<count;k++){double r=radius-4*band*k;if(r<0)continue;double p=nrClamp(1-nrAbs(distance-r)/band,0,1),v=p*p*(3-2*p)/(1+.42*k);if(v>value)value=v;}
        value*=fade*fade*(3-2*fade);
    }else if(profile==2){double d=(distance-radius)/band;if(nrAbs(d)<=3)value=nrPowPositive(.3678794411714423216,d*d)*fade*fade*.65;}
    else if(profile==3)value=nrPowPositive(fade,1.5);
    else if(profile==4)value=nrClamp(1-nrAbs(distance-radius)/band,0,1)*nrPowPositive(fade,1.8)*.35;
    if(q->materialAuthored)*color=nrPaint(s,f->material,s->timeUs,distance*.5*q->frequency/100,&alpha);
    else if(profile==1)*color=silkColor(f,q,distance);
    else {double hue=(profile==2?f->id*53.0+age*20:profile==3?290:60)+q->phase;hue=nrFloor(hue+.5);hue-=360*nrFloor(hue/360);*color=nrOklch(830000,100000,(int32_t)(hue*1000));}
    *intensity=value*f->strength*alpha;
}
int nrSourceFieldHit(const State*s,int i,double x,double y){
    const Field*f=&s->fields[i];const FieldControls*q=&s->fieldControls[i];double cx,cy;nrFieldCenter(s,i,&cx,&cy);
    double age=(s->timeUs-f->atUs)/1e6,radius=q->continuous?0:2*age*f->speed;
    double px=nrFloor(2*x+.5),py=nrFloor(4*y+.5),ox=2*cx,oy=4*cy;
    for(int j=0;j<96;j++)if(px==nrFloor(ox+radius*nrCos(j*3.75)+.5)&&py==nrFloor(oy+radius*nrSin(j*3.75)+.5))return 1;
    return 0;
}
