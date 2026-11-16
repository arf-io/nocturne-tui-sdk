#include "internal.h"
#include "window_palette_source.h"
#include "window_source_math.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double low,double high){int t=nrField(j,0,key);if(t<0)return 1;double v;if(!nrNumber(j,t,&v)||!(v>=low&&v<=high))return 0;*out=v;return 1;}
int nrObservatoryProfile(const State*s,int slot){
    if(slot<0||slot>=(int)NR_MAX_EMITTERS||!s->emitters[slot].used)return -1;
    const char*name=nrEffectName(s->emitters[slot].effect);
    const char*names[]={"weather/rain-threads","weather/snow-dust","weather/lantern-motes","weather/pinfire"};
    for(int i=0;i<4;i++)if(!strcmp(name,names[i]))return i;return -1;
}
int nrValidObservatoryControls(const State*s){
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        const ObservatoryControls*b=&s->observatoryControls[slot];
        if(!b->used){if(b->generation||b->seed||b->reserved||b->speed||b->intensity||b->durationUs||b->startUs)return 0;continue;}
        if(b->used!=1||b->reserved>1||(b->reserved&&s->schema<NR_STATE_SCHEMA_OBSERVATORY_PAINT)||s->schema<NR_STATE_SCHEMA_OBSERVATORY||nrObservatoryProfile(s,slot)<0||
           b->generation!=s->emitters[slot].generation||!(b->speed>=0&&b->speed<=10000)||!(b->intensity>=0&&b->intensity<=1)||
           !b->durationUs||b->durationUs>60000000||b->startUs>s->timeUs)return 0;
    }return 1;
}
int nrObservatoryStyleCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_OBSERVATORY)return reject(c,"Observatory style requires schema58");
    int removal=nrEqual(j,nrField(j,0,"op"),"remove-observatory-style");
    if(!nrAllowed(j,0,removal?"op id":"op id seed speed intensity durationMs paint"))return reject(c,"Unknown Observatory setting");
    double id=0;if(nrField(j,0,"id")<0||!number(j,"id",&id,1,65535)||id!=(uint32_t)id)return reject(c,"Observatory emitter id required");
    int slot=nrFindEmitter(s,(int)id);if(nrObservatoryProfile(s,slot)<0)return reject(c,"Observatory style requires source weather emitter");
    if(removal){memset(&s->observatoryControls[slot],0,sizeof(ObservatoryControls));return 0;}
    ObservatoryControls b=s->observatoryControls[slot];
    if(!b.used)b=(ObservatoryControls){.used=1,.reserved=1,.generation=s->emitters[slot].generation,.seed=s->emitters[slot].seed,.speed=12,.intensity=.5,.durationUs=2400000,.startUs=s->timeUs};
    int paint=nrField(j,0,"paint");if(paint>=0){if(nrEqual(j,paint,"source"))b.reserved=1;else if(nrEqual(j,paint,"material"))b.reserved=0;else return reject(c,"Invalid Observatory painting mode");}
    if(b.reserved&&s->schema<NR_STATE_SCHEMA_OBSERVATORY_PAINT)return reject(c,"Observatory painting requires schema83");
    double duration=b.durationUs/1000.0,seed=b.seed;
    if(!number(j,"speed",&b.speed,0,10000)||!number(j,"intensity",&b.intensity,0,1)||!number(j,"seed",&seed,0,4294967295.0)||seed!=(uint32_t)seed||
       !number(j,"durationMs",&duration,.001,60000)||duration*1000!=(uint64_t)(duration*1000))return reject(c,"Invalid Observatory setting");
    b.seed=(uint32_t)seed;b.durationUs=(uint64_t)(duration*1000);s->observatoryControls[slot]=b;return 0;
}
static double randomAt(uint32_t seed,uint32_t index){return nrHash(seed^((index+1u)*2654435769u))/4294967296.0;}
int nrObservatorySample(const State*s,int slot,int index,double out[5]){
    int kind=nrObservatoryProfile(s,slot);if(!out||kind<0)return 0;
    const ObservatoryControls*b=&s->observatoryControls[slot];
    if(!b->used||b->generation!=s->emitters[slot].generation||index<0||index>=(int)(16+24*b->intensity+.5))return 0;
    uint64_t elapsed=s->timeUs>=b->startUs?s->timeUs-b->startUs:0;if(elapsed>=b->durationUs)return 0;
    double t=elapsed/1000000.0,r=randomAt(b->seed,(uint32_t)index),r2=randomAt(b->seed+7919u,(uint32_t)index),x=0,y=0;uint32_t glyph=0xb7;
    if(kind==0){x=(r-.5)*20;y=-r2*14+t*b->speed;glyph=index%2?0x2571:0x2502;}
    else if(kind==1){x=(r-.5)*24+(b->reserved?nrWindowSourceSin(2*t+r2*2*NR_PI):nrSin((2*t+r2*2*NR_PI)*180/NR_PI))*2;y=-12-r2*8+t*b->speed*.4;glyph=(const uint32_t[]){0xb7,0x2219,0x22c5}[index%3];}
    else if(kind==2){x=(r-.5)*t*8;y=-t*b->speed*(.2+r2*.4);glyph=0x2219;}
    else{x=(b->reserved?nrWindowSourceCos(r*2*NR_PI):nrCos(r*360))*t*b->speed*r2;y=(b->reserved?nrWindowSourceSin(r*2*NR_PI):nrSin(r*360))*t*b->speed*r2*.5+t*t*2;}
    double remaining=1-(double)elapsed/b->durationUs;
    out[0]=index;out[1]=x;out[2]=y;out[3]=glyph;out[4]=b->reserved?b->intensity*(remaining*remaining)*(.5+.5*r):b->intensity*remaining*remaining*(.5+.5*r);return 1;
}
int nrObservatoryCenter(const State*s,int slot,double out[3]){
    if(!out||nrObservatoryProfile(s,slot)<0||!s->observatoryControls[slot].used)return 0;
    int width,height;nrSceneViewport(s,&width,&height);
    Projection p;nrProjection(s,width,height,&p);int visible=nrProject(&p,s->emitters[slot].position,&out[0],&out[1],&out[2]);
    if(visible){out[0]*=.5;out[1]*=.25;}return visible;
}
static uint32_t mix(uint32_t a,uint32_t b,double t){
    t=nrClamp(t,0,1);uint32_t out=0;for(int shift=0;shift<=16;shift+=8){double aa=(a>>shift)&255,bb=(b>>shift)&255;out|=(uint32_t)nrFloor(aa*(1-t)+bb*t+.5)<<shift;}return out;
}
static uint32_t flattened(const NrCell*c){return c->glyph==0x2580||c->glyph==0x2584||c->glyph==0x258c||c->glyph==0x2590?mix(c->foreground,c->background,.5):c->background;}
static void originalPaint(NrContext*c,const State*s,int slot,const double center[3],double weight){
    if(weight<=0)return;const ObservatoryControls*b=&s->observatoryControls[slot];uint64_t elapsed=s->timeUs-b->startUs;if(elapsed>=b->durationUs||b->intensity==0)return;
    double hue=b->seed*53.0+(double)elapsed/1000*.02;int h=(int)(nrFloor(hue+.5)-360*nrFloor(nrFloor(hue+.5)/360));uint32_t color;
    if(nrWindowPaletteSourceTextInk(.83,.1,h,&color))return;
    /* Original local layer starts transparent black. Repeated particles replace
     * the same tile cell before that final cell is composited onto the host. */
    uint32_t glyphs[80*44]={0},colors[80*44]={0};int count=(int)(16+24*b->intensity+.5);
    for(int index=0;index<count;index++){
        double row[5];if(!nrObservatorySample(s,slot,index,row))break;double x=nrFloor(40+row[1]),y=nrFloor(22+row[2]);
        if(x<0||y<0||x>=80||y>=44)continue;size_t i=(size_t)y*80+(size_t)x;glyphs[i]=(uint32_t)row[3];colors[i]=mix(0,color,row[4]);
    }
    for(int y=0;y<44;y++)for(int x=0;x<80;x++){
        size_t i=(size_t)y*80+x;if(!colors[i])continue;double xx=nrFloor(center[0]+x-40+.5),yy=nrFloor(center[1]+y-22+.5);
        if(xx<0||yy<0||xx>=s->width||yy>=s->height)continue;NrCell*d=&c->cells[(size_t)yy*s->width+(size_t)xx];uint32_t bg=flattened(d);
        d->glyph=glyphs[i];d->foreground=mix(bg,colors[i],.95*weight);d->background=bg;d->id=0;
    }
}
void nrDrawObservatory(NrContext*c,const Projection*projection){
    const State*s=nrView(c);
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        if(!s->observatoryControls[slot].used)continue;
        double center[3];if(!nrProject(projection,s->emitters[slot].position,&center[0],&center[1],&center[2]))continue;
        center[0]*=.5;center[1]*=.25;const Emitter*e=&s->emitters[slot];
        double materialAlpha;uint32_t color=nrPaint(s,e->material,s->timeUs,(uint32_t)e->id,&materialAlpha);
        nrUseMaterial(c,e->material);c->characterOwner=0;
        if(s->observatoryControls[slot].reserved){originalPaint(c,s,slot,center,e->alpha*materialAlpha);continue;}
        int count=(int)(16+24*s->observatoryControls[slot].intensity+.5);
        for(int index=0;index<count;index++){
            double row[5];if(!nrObservatorySample(s,slot,index,row))break;
            double x=nrFloor(center[0]+row[1]),y=nrFloor(center[1]+row[2]);
            if(x<0||y<0||x>=s->width||y>=s->height)continue;
            uint32_t ink=color;if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,(int32_t)x*256,(int32_t)y*256,(uint32_t)index,&ignored);}
            nrIndexedGlyph(c,(int)x,(int)y,(uint32_t)row[3],ink,row[4]*e->alpha*materialAlpha,0,(uint32_t)index);
        }
    }c->paintBlend=0;
}
