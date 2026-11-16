#include "internal.h"
void nrFieldControlsInit(FieldControls*q){
    if(q->used)return;memset(q,0,sizeof(*q));q->used=1;q->falloff=2;q->frequency=100;
}
int nrFieldLive(const State*s,int i){
    const Field*f=&s->fields[i];return f->used&&s->timeUs>=f->atUs&&(s->fieldControls[i].continuous||s->timeUs-f->atUs<f->lifeUs);
}
void nrFieldCenter(const State*s,int i,double*x,double*y){
    const Field*f=&s->fields[i];const FieldControls*q=&s->fieldControls[i];double age=(s->timeUs-f->atUs)/1e6;
    *x=f->x+age*q->vx+(q->surface?q->x:0);*y=f->y+age*q->vy+(q->surface?q->y:0);
}
int nrFieldContains(const State*s,int i,double x,double y){
    const FieldControls*q=&s->fieldControls[i];return !q->surface||(x>=q->x&&x<q->x+q->width&&y>=q->y&&y<q->y+q->height);
}
void nrFieldCurve(const State*s,int i,double dist,uint32_t*color,double*intensity){
    const Field*f=&s->fields[i];const FieldControls*q=&s->fieldControls[i];if(NR_FIELD_OPTICS(q)){nrSourceFieldCurve(s,i,dist,color,intensity);return;}double age=(s->timeUs-f->atUs)/1e6;
    double band=f->width*2,radius=q->continuous?0:age*f->speed*2,d=dist-radius;
    int algorithm=nrEffectAlgorithm(f->effect),falloff=q->used?q->falloff:2;
    double frequency=q->used?q->frequency:100,angle=(dist-age*f->speed*2)/(band+.01)*frequency-age*90+q->phase+algorithm*35;
    double wave=.5+.5*nrCos(angle);
    if(q->interference)wave=wave*(1-q->interference)+q->interference*(.5+.5*nrCos(2*angle+f->seed%360));
    double envelope;
    if(falloff==2)envelope=1/(1+d*d/(band*band));
    else {double power=1,normalized=nrAbs(d/band);for(int j=0;j<falloff;j++)power*=normalized;envelope=1/(1+power);}
    double fade=q->continuous?1:1-age/(f->lifeUs/1e6),alpha=1;
    double hue=dist*3+algorithm*55+220+age*35;if(hue>2000000||hue< -2000000)hue-=360*nrFloor(hue/360);
    *color=q->materialAuthored?nrPaint(s,f->material,s->timeUs,f->id,&alpha):nrOklch((int32_t)((.62+.12*wave)*1e6),(int32_t)((.05+.04*wave)*1e6),(int32_t)(hue*1000));
    if(NR_FIELD_RINGS(q)){
        double peak=0;for(uint32_t k=0;k<NR_FIELD_RINGS(q);k++){double r=radius-4*band*k;if(r<0)continue;double p=nrClamp(1-nrAbs(dist-r)/band,0,1);double v=p*p*(3-2*p)/(1+.42*k);if(v>peak)peak=v;}
        double p=nrClamp(fade,0,1);*intensity=peak*p*p*(3-2*p)*f->strength*alpha;
    }else *intensity=envelope*(.2+.8*wave)*fade*f->strength*alpha;
}
static int32_t fieldQ8(double coordinate){
    double q=coordinate*256;
    if(q<INT32_MIN)return INT32_MIN;if(q>INT32_MAX)return INT32_MAX;
    return (int32_t)q;
}
void nrFieldCurveAt(const State*s,int i,double dist,int32_t xQ8,int32_t yQ8,uint32_t*color,double*intensity){
    if(i<0||i>=NR_FIELDS)return;
    nrFieldCurve(s,i,dist,color,intensity);
    if(!s->fieldControls[i].materialAuthored)return;
    int material=s->fields[i].material;
    if(material<0||material>=NR_MATERIALS||!s->materialPatterns[material].used)return;
    double ignored;*color=nrPaintAt(s,material,s->timeUs,xQ8,yQ8,s->fields[i].id,&ignored);
}
int nrFieldSample(const NrContext*c,uint32_t id,double x,double y,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||!id||id==0xffffffffu||!(x>=NR_LAYOUT_MIN&&x<=NR_LAYOUT_MAX)||!(y>=NR_LAYOUT_MIN&&y<=NR_LAYOUT_MAX)||!out||capacity<4||((uintptr_t)out%8)||!nrExternalOutput(c,out,4*sizeof(double)))return -1;
    const State*s=&c->state;
    for(int i=0;i<NR_FIELDS;i++)if(s->fields[i].id==id&&nrFieldLive(s,i)){
        double cx,cy;nrFieldCenter(s,i,&cx,&cy);double dx=2*(x-cx),dy=4*(y-cy),dist=nrSqrt(dx*dx+dy*dy),age=(s->timeUs-s->fields[i].atUs)/1e6;
        double radius=s->fieldControls[i].continuous?0:2*age*s->fields[i].speed;uint32_t rgb;double value;
        nrFieldCurveAt(s,i,dist,fieldQ8(x),fieldQ8(y),&rgb,&value);
        if(NR_FIELD_OPTICS(&s->fieldControls[i])==3&&!nrSourceFieldHit(s,i,x,y))value=0;
        if(!nrFieldContains(s,i,x,y)||(!NR_FIELD_OPTICS(&s->fieldControls[i])&&!NR_FIELD_RINGS(&s->fieldControls[i])&&nrAbs(dist-radius)>s->fields[i].width*10))value=0;
        double row[4]={value,rgb,cx,cy};memcpy(out,row,sizeof(row));return 1;
    }
    return 0;
}
static int finiteRange(double x,double lo,double hi){return x>=lo&&x<=hi;}
int nrValidFieldControls(const State*s){
    for(int i=0;i<NR_FIELDS;i++){
        const FieldControls*q=&s->fieldControls[i];FieldControls zero={0};
        if(!q->used){if(memcmp(q,&zero,sizeof(*q)))return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_COLOR_FIELDS||!s->fields[i].used||q->used!=1||q->continuous<0||q->continuous>1||q->materialAuthored<0||q->materialAuthored>1||q->surface<0||q->surface>1||NR_FIELD_RINGS(q)>16||(q->rings&192u)||NR_FIELD_OPTICS(q)>4||(NR_FIELD_OPTICS(q)&&(s->schema<NR_STATE_SCHEMA_SOURCE_OPTICS||NR_FIELD_OPTICS(q)!=(uint32_t)nrEffectAlgorithm(s->fields[i].effect)+1))||(NR_FIELD_OPTICS(q)>1&&NR_FIELD_RINGS(q))||(NR_FIELD_RINGS(q)&&s->schema<NR_STATE_SCHEMA_SOFT_FRONTS)||q->falloff<1||q->falloff>8||!finiteRange(q->frequency,0,1000)||!finiteRange(q->phase,-3600,3600)||!finiteRange(q->interference,0,1)||!finiteRange(q->vx,-100,100)||!finiteRange(q->vy,-100,100)||!finiteRange(q->x,NR_LAYOUT_MIN,NR_LAYOUT_MAX)||!finiteRange(q->y,NR_LAYOUT_MIN,NR_LAYOUT_MAX))return 0;
        if(!nrValidOriginalField(s,i))return 0;
        if(q->surface){if(!finiteRange(q->width,.05,NR_LAYOUT_MAX)||!finiteRange(q->height,.05,NR_LAYOUT_MAX))return 0;}
        else if(q->x||q->y||q->width||q->height)return 0;
    }return 1;
}
