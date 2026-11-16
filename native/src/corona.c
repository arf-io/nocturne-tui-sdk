#include "internal.h"
#include "window_palette_source.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double low,double high){
    int t=nrField(j,0,key);if(t<0)return 1;double value;
    if(!nrNumber(j,t,&value)||!(value>=low&&value<=high))return 0;*out=value;return 1;
}
static int coronaEmitter(const State*s,int slot){
    return slot>=0&&slot<(int)NR_MAX_EMITTERS&&s->emitters[slot].used&&
        !strcmp(nrEffectName(s->emitters[slot].effect),"weather/corona-flare");
}
int nrValidCoronaControls(const State*s){
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++){
        const CoronaControls*b=&s->coronaControls[i];
        if(!b->used){if(b->generation||b->speed||b->width||b->intensity||b->durationUs||b->startUs)return 0;continue;}
        if((b->used!=1&&b->used!=2)||(b->used==2&&s->schema<NR_STATE_SCHEMA_CORONA_PAINT)||s->schema<NR_STATE_SCHEMA_CORONA||!coronaEmitter(s,i)||
           b->generation!=s->emitters[i].generation||!(b->speed>=0&&b->speed<=10000)||
           !(b->width>=.001&&b->width<=10000)||!(b->intensity>=0&&b->intensity<=1)||
           !b->durationUs||b->durationUs>60000000||b->startUs>s->timeUs)return 0;
    }return 1;
}
int nrCoronaStyleCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_CORONA)return reject(c,"Corona style requires schema57");
    int removal=nrEqual(j,nrField(j,0,"op"),"remove-corona-style");
    if(!nrAllowed(j,0,removal?"op id":"op id speed width intensity durationMs paint"))return reject(c,"Unknown corona setting");
    double id=0;if(nrField(j,0,"id")<0||!number(j,"id",&id,1,65535)||id!=(uint32_t)id)return reject(c,"Corona emitter id required");
    int slot=nrFindEmitter(s,(int)id);if(!coronaEmitter(s,slot))return reject(c,"Corona style requires Corona Flare emitter");
    if(removal){memset(&s->coronaControls[slot],0,sizeof(CoronaControls));return 0;}
    CoronaControls b=s->coronaControls[slot];
    if(!b.used)b=(CoronaControls){.used=2,.generation=s->emitters[slot].generation,.speed=12,.width=1.7,.intensity=.28,.durationUs=2400000,.startUs=s->timeUs};
    int paint=nrField(j,0,"paint");if(paint>=0){if(nrEqual(j,paint,"source"))b.used=2;else if(nrEqual(j,paint,"material"))b.used=1;else return reject(c,"Invalid Corona painting mode");}
    if(b.used==2&&s->schema<NR_STATE_SCHEMA_CORONA_PAINT)return reject(c,"Corona painting requires schema84");
    double duration=b.durationUs/1000.0;
    if(!number(j,"speed",&b.speed,0,10000)||!number(j,"width",&b.width,.001,10000)||
       !number(j,"intensity",&b.intensity,0,1)||!number(j,"durationMs",&duration,.001,60000)||
       duration*1000!=(uint64_t)(duration*1000))return reject(c,"Invalid corona setting");
    b.durationUs=(uint64_t)(duration*1000);s->coronaControls[slot]=b;return 0;
}
static double expNegative(double x){
    if(x>745)return 0;int squares=0;while(x>.125){x*=.5;squares++;}
    double result=1,term=1;for(int i=1;i<=20;i++){term*= -x/i;result+=term;}
    for(int i=0;i<squares;i++)result*=result;return result;
}
static double gaussian(double x){return expNegative(x*x);}
/* Pure outputs: elapsed microseconds, radius, envelope, core scalar, ring alpha.
 * Distance is the original terminal-cell radial metric, not a native path sample. */
int nrCoronaAppearance(const State*s,int slot,double distance,double out[5]){
    if(!out||!coronaEmitter(s,slot)||!s->coronaControls[slot].used||!(distance>=0&&distance<=1e12))return 0;
    const CoronaControls*b=&s->coronaControls[slot];if(b->generation!=s->emitters[slot].generation)return 0;
    uint64_t elapsed=s->timeUs>=b->startUs?s->timeUs-b->startUs:0;
    double remaining=elapsed<b->durationUs?1-(double)elapsed/b->durationUs:0;
    out[0]=(double)elapsed;out[1]=b->speed*elapsed/1000000.0;out[2]=remaining*remaining;
    out[3]=remaining>0?(elapsed<200000?0x2219:elapsed<430000?0x2726:elapsed<650000?0x2727:0):0;
    out[4]=gaussian((distance-out[1])/b->width)*b->intensity*out[2]*.65;return 1;
}
int nrCoronaCenter(const State*s,int slot,double out[3]){
    if(!out||!coronaEmitter(s,slot)||!s->coronaControls[slot].used)return 0;
    int width,height;nrSceneViewport(s,&width,&height);
    Projection p;nrProjection(s,width,height,&p);
    int visible=nrProject(&p,s->emitters[slot].position,&out[0],&out[1],&out[2]);
    if(visible){out[0]*=.5;out[1]*=.25;}return visible;
}
static uint32_t sourceMix(uint32_t a,uint32_t b,double t){
    t=nrClamp(t,0,1);uint32_t out=0;for(int shift=0;shift<=16;shift+=8){double aa=(a>>shift)&255,bb=(b>>shift)&255;out|=(uint32_t)nrFloor(aa*(1-t)+bb*t+.5)<<shift;}return out;
}
static uint32_t flattened(const NrCell*c){return c->glyph==0x2580||c->glyph==0x2584||c->glyph==0x258c||c->glyph==0x2590?sourceMix(c->foreground,c->background,.5):c->background;}
/* ObservatoryRenderer.weather authors a transparent 80x44 local tile. Its
 * EffectPainter.local compositor then flattens the destination and applies
 * separate .7 background / .95 foreground weights. Width remains an additive
 * SDK control; the original author's width is exactly 1.7. */
static void originalPaint(NrContext*c,const State*s,int slot,const double center[3],double weight){
    const CoronaControls*b=&s->coronaControls[slot];uint64_t elapsed=s->timeUs-b->startUs;
    if(weight<=0||elapsed>=b->durationUs||b->intensity==0)return;
    double age=(double)elapsed/1000,remaining=1-age/(b->durationUs/1000.0),strength=b->intensity*(remaining*remaining);
    double radius=age/1000*b->speed,extent=radius+b->width*3,hue=s->emitters[slot].id*53.0+age*.02;
    int h=(int)(nrFloor(hue+.5)-360*nrFloor(nrFloor(hue+.5)/360));uint32_t color;
    if(nrWindowPaletteSourceTextInk(.83,.1,h,&color))return;
    for(int y=0;y<44;y++)for(int x=0;x<80;x++){
        uint32_t bg=0,fg=0,glyph=32;
        if(y>=nrFloor(22-extent/2)&&y<22+extent/2&&x>=nrFloor(40-extent)&&x<40+extent){
            double dx=x-40,dy=(y+.5-22)*2,ring=nrSqrt(dx*dx+dy*dy)-radius;
            bg=sourceMix(0,color,expNegative(ring*ring/(b->width*b->width))*strength*.65);
        }
        if(x==40&&y==22&&age<650){glyph=age<200?0x2219:age<430?0x2726:0x2727;fg=sourceMix(bg,color,strength);}
        if(!bg&&(glyph==32||!fg))continue;
        double xx=nrFloor(center[0]+x-40+.5),yy=nrFloor(center[1]+y-22+.5);
        if(xx<0||yy<0||xx>=s->width||yy>=s->height)continue;
        NrCell*d=&c->cells[(size_t)yy*s->width+(size_t)xx];
        if(bg)d->background=sourceMix(flattened(d),bg,.7*weight);
        if(glyph!=32&&fg){uint32_t under=flattened(d);d->glyph=glyph;d->foreground=sourceMix(under,fg,.95*weight);d->background=under;d->id=0;}
    }
}
/* Resolve the source optical treatment after world fragments and before local UI.
 * Existing half-blocks retain their separate quarter/three-quarter sample colors. */
void nrDrawCorona(NrContext*c,const Projection*projection){
    const State*s=nrView(c);
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        double center[3],sample[5];
        if(!nrCoronaAppearance(s,slot,0,sample)||sample[2]<=0||!nrProject(projection,s->emitters[slot].position,&center[0],&center[1],&center[2]))continue;
        center[0]*=.5;center[1]*=.25;
        const CoronaControls*b=&s->coronaControls[slot];const Emitter*e=&s->emitters[slot];
        double materialAlpha;uint32_t color=nrPaint(s,e->material,s->timeUs,(uint32_t)e->id,&materialAlpha);
        double alpha=e->alpha*materialAlpha,extent=sample[1]+3*b->width;
        if(b->used==2){originalPaint(c,s,slot,center,alpha);continue;}
        double left=nrClamp(center[0]-extent,0,s->width),right=nrClamp(center[0]+extent+1,0,s->width);
        double top=nrClamp(center[1]-extent*.5,0,s->height),bottom=nrClamp(center[1]+extent*.5+1,0,s->height);
        for(int y=(int)nrFloor(top);y<(int)bottom;y++)for(int x=(int)nrFloor(left);x<(int)right;x++){
            NrCell*cell=&c->cells[(size_t)y*s->width+x];
            double dx=x-center[0],dy=2*(y+(cell->glyph==0x2580?.25:.5)-center[1]);
            nrCoronaAppearance(s,slot,nrSqrt(dx*dx+dy*dy),sample);
            uint32_t localColor=color;if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;localColor=nrPaintAt(s,e->material,s->timeUs,x*256,y*256,0,&ignored);}
            if(cell->glyph==0x2580){cell->foreground=nrMix(cell->foreground,localColor,sample[4]*alpha);
                dy=2*(y+.75-center[1]);nrCoronaAppearance(s,slot,nrSqrt(dx*dx+dy*dy),sample);}
            cell->background=nrMix(cell->background,localColor,sample[4]*alpha);
        }
        nrCoronaAppearance(s,slot,0,sample);
        if(sample[3]&&center[0]>=0&&center[0]<s->width&&center[1]>=0&&center[1]<s->height){uint32_t ink=color;if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,(int32_t)center[0]*256,(int32_t)center[1]*256,0,&ignored);}nrGlyph(c,(int)center[0],(int)center[1],(uint32_t)sample[3],ink,b->intensity*sample[2]*alpha,0);}
    }
}
