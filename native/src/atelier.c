#include "internal.h"
#include "window_palette_source.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double lo,double hi){int t=nrField(j,0,key);if(t<0)return 1;double v;if(!nrNumber(j,t,&v)||!(v>=lo&&v<=hi))return 0;*out=v;return 1;}
static int integer(const Json*j,const char*key,uint32_t*out,uint32_t lo,uint32_t hi){double v=*out;if(!number(j,key,&v,lo,hi)||v!=(uint32_t)v)return 0;*out=(uint32_t)v;return 1;}
int nrAtelierProfile(const State*s,int slot){
    if(slot<0||slot>=(int)NR_MAX_EMITTERS||!s->emitters[slot].used)return -1;
    const char*names[]={"weather/fractured-sun","weather/livewire","weather/copper-cinders","weather/slantfall","weather/crystalline-drift"};
    for(int i=0;i<5;i++)if(!strcmp(nrEffectName(s->emitters[slot].effect),names[i]))return i;return -1;
}
static int valid(const AtelierControls*b){
    if(b->used!=1||b->reserved>1||b->count>256||b->branches<1||b->branches>20||b->reducedMotion>1)return 0;
#define RANGE(name,lo,hi) if(!(b->name>=lo&&b->name<=hi))return 0
    RANGE(lifeMs,200,10000);RANGE(speed,0,70);RANGE(gravity,0,35);RANGE(rise,0,40);RANGE(drag,0,3);RANGE(turbulence,0,8);
    RANGE(glitterHz,1,30);RANGE(trailMs,0,400);RANGE(jaggedness,0,8);RANGE(coreMs,0,600);RANGE(coreRadius,0,6);
    RANGE(ejecta,0,2);RANGE(shockwave,0,1);RANGE(intensity,0,1);
#undef RANGE
    return 1;
}
int nrValidAtelierControls(const State*s){
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        const AtelierControls*b=&s->atelierControls[slot];
        if(!b->used){const unsigned char*p=(const unsigned char*)b;for(size_t i=0;i<sizeof(*b);i++)if(p[i])return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_ATELIER||nrAtelierProfile(s,slot)<0||!valid(b)||b->generation!=s->emitters[slot].generation||b->startUs>s->timeUs)return 0;
    }return 1;
}
int nrAtelierStyleCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_ATELIER)return reject(c,"Atelier style requires schema60");
    int removal=nrEqual(j,nrField(j,0,"op"),"remove-atelier-style");
    if(!nrAllowed(j,0,removal?"op id":"op id lifeMs count speed gravity rise drag turbulence glitterHz trailMs branches jaggedness coreMs coreRadius ejecta shockwave intensity seed eventId reducedMotion paint"))return reject(c,"Unknown Atelier setting");
    uint32_t id=0;if(nrField(j,0,"id")<0||!integer(j,"id",&id,1,65535))return reject(c,"Atelier emitter id required");
    int slot=nrFindEmitter(s,(int)id);if(nrAtelierProfile(s,slot)<0)return reject(c,"Atelier style requires source weather emitter");
    if(removal){memset(&s->atelierControls[slot],0,sizeof(AtelierControls));return 0;}
    AtelierControls b=s->atelierControls[slot];if(!b.used)b=(AtelierControls){.used=1,.generation=s->emitters[slot].generation,.reserved=1,.seed=4711,.eventId=id,.count=64,.branches=7,
        .lifeMs=4200,.speed=20,.gravity=9,.rise=10,.drag=.22,.turbulence=1.3,.glitterHz=14,.trailMs=100,.jaggedness=2.2,.coreMs=280,.coreRadius=3,.ejecta=1,.shockwave=0,.intensity=.8,.startUs=s->timeUs};
    int paint=nrField(j,0,"paint");if(paint>=0){if(nrEqual(j,paint,"source"))b.reserved=1;else if(nrEqual(j,paint,"material"))b.reserved=0;else return reject(c,"Invalid Atelier painting mode");}
    if(!integer(j,"count",&b.count,0,256)||!integer(j,"branches",&b.branches,1,20)||!integer(j,"seed",&b.seed,0,0xffffffffu)||!integer(j,"eventId",&b.eventId,0,0xffffffffu))return reject(c,"Invalid Atelier integer");
#define FIELD(name,lo,hi) if(!number(j,#name,&b.name,lo,hi))return reject(c,"Invalid Atelier setting")
    FIELD(lifeMs,200,10000);FIELD(speed,0,70);FIELD(gravity,0,35);FIELD(rise,0,40);FIELD(drag,0,3);FIELD(turbulence,0,8);
    FIELD(glitterHz,1,30);FIELD(trailMs,0,400);FIELD(jaggedness,0,8);FIELD(coreMs,0,600);FIELD(coreRadius,0,6);FIELD(ejecta,0,2);FIELD(shockwave,0,1);FIELD(intensity,0,1);
#undef FIELD
    int at=nrField(j,0,"reducedMotion"),motion=(int)b.reducedMotion;if(at>=0&&!nrBoolean(j,at,&motion))return reject(c,"Atelier reducedMotion Boolean required");b.reducedMotion=(uint32_t)motion;
    if(!valid(&b))return reject(c,"Invalid Atelier controls");s->atelierControls[slot]=b;return 0;
}
static double decay(double x){
    if(x>745)return 0;int squares=0;while(x>.125){x*=.5;squares++;}
    double result=1,term=1;for(int i=1;i<=20;i++){term*= -x/i;result+=term;}
    for(int i=0;i<squares;i++)result*=result;return result;
}
static double power18(double x){
    if(x<=0)return 0;if(x>=1)return 1;int exponent=0;while(x<.75){x*=2;exponent--;}
    double z=(x-1)/(x+1),square=z*z,term=z,sum=z;
    for(int i=3;i<=39;i+=2){term*=square;sum+=term/i;}
    return decay(-1.8*(2*sum+exponent*.6931471805599453094));
}
static double randomAt(uint32_t seed,uint32_t index){return nrHash(seed^((index+1u)*2654435769u))/4294967296.0;}
static void point(AtelierSample*out,const AtelierControls*b,double x,double y,uint32_t glyph,double alpha,double heat){
    if(out->pointCount>=513)return;double*r=out->points[out->pointCount++];r[0]=x;r[1]=y;r[2]=glyph;r[3]=nrClamp(alpha*b->intensity,0,1);r[4]=nrClamp(heat,0,1);
}
static void segment(AtelierSample*out,const AtelierControls*b,double x,double y,double xx,double yy,double alpha,double heat){
    if(out->segmentCount>=524)return;double*r=out->segments[out->segmentCount++];r[0]=x;r[1]=y;r[2]=xx;r[3]=yy;r[4]=nrClamp(alpha*b->intensity,0,1);r[5]=nrClamp(heat,0,1);
}
static void glow(AtelierSample*out,double radius,double alpha,double heat,int ring){
    if(out->glowCount>=2)return;double*r=out->glows[out->glowCount++];r[0]=r[1]=0;r[2]=radius;r[3]=alpha;r[4]=heat;r[5]=ring;
}
static void ember(const AtelierControls*b,double r,double r2,double t,double out[2]){
    out[0]=(r-.5)*b->speed*t/(1+b->drag*t)+nrSin((t*2+r2*2*NR_PI)*180/NR_PI)*b->turbulence*t;
    out[1]=-b->rise*(.6+r2*.4)*t+.5*b->gravity*t*t;
}
int nrAtelierSample(const State*s,int slot,AtelierSample*out){
    int kind=nrAtelierProfile(s,slot);if(!out||kind<0||!s->atelierControls[slot].used)return 0;
    const AtelierControls*b=&s->atelierControls[slot];if(b->generation!=s->emitters[slot].generation)return 0;
    return nrAtelierSampleAt(b,kind,(double)(s->timeUs-b->startUs)/1000,out);
}
int nrAtelierSampleAt(const AtelierControls*b,int kind,double age,AtelierSample*out){
    if(!b||!out||kind<0||kind>5||!valid(b))return 0;memset(out,0,sizeof(*out));
    if(age<0||age>=b->lifeMs||b->reducedMotion||b->intensity==0)return 1;
    double t=age/1000,p=age/b->lifeMs,fade=power18(1-p);uint32_t seed=b->eventId^b->seed;
    if(kind==1){
        double strike=b->lifeMs<1100?b->lifeMs:1100,a=nrClamp(1-age/strike,0,1);if(a==0)return 1;
        double period=1000/b->glitterHz;if(period<34)period=34;uint32_t flash=(uint32_t)nrFloor(age/period);
        double jitter=.65+.35*randomAt(seed,flash+901);
        for(uint32_t branch=0;branch<b->branches;branch++){
            double angle=randomAt(seed,branch*41)*360,length=b->speed*(.2+.8*randomAt(seed,branch*41+1))*(.45+.55*nrClamp(t*8,0,1)),x=0,y=0;
            for(uint32_t j=1;j<=8;j++){
                double q=j/8.0,kink=(randomAt(seed^(branch+17),flash*97+j)-.5)*b->jaggedness*nrSin(q*180);
                double xx=nrCos(angle)*length*q+nrSin(angle)*kink,yy=nrSin(angle)*length*q*.5-nrCos(angle)*kink*.5;
                segment(out,b,x,y,xx,yy,a*jitter*(1-q*.4),.8+q*.2);
                if(j==4||j==6){double fork=angle+(j==4?.8:-.8)*180/NR_PI,r=length*.28;segment(out,b,xx,yy,xx+nrCos(fork)*r,yy+nrSin(fork)*r*.5,a*.6,.65);}
                x=xx;y=yy;
            }
            point(out,b,x,y,flash%3==0?0x2727:0xb7,a,.98);
        }
        glow(out,1.2,a*.3*b->intensity,1,0);return 1;
    }
    if(kind==0){
        double core=b->coreMs?nrClamp(1-age/b->coreMs,0,1):0;
        if(core>0)glow(out,b->coreRadius*(.5+age/(b->coreMs>1?b->coreMs:1)),core*.8*b->intensity,1,0);
        uint32_t count=(uint32_t)nrFloor(b->count*b->ejecta);
        for(uint32_t j=0;j<count;j++){
            double a=randomAt(seed,j*13)*360,v=b->speed*(.28+randomAt(seed,j*13+1)),radius=v*(1-decay(t*.7))/.7;
            double x=nrCos(a)*radius,y=nrSin(a)*radius*.5+.2*t*t,tail=nrClamp(t-b->trailMs/1000,0,1e12),r0=v*(1-decay(tail*.7))/.7;
            double flicker=randomAt(seed+j,(uint32_t)nrFloor(t*b->glitterHz)),alpha=fade*(.25+.75*flicker),heat=nrClamp(1-p*.8-(double)j/b->count*.2,0,1);
            segment(out,b,nrCos(a)*r0,nrSin(a)*r0*.5,x,y,alpha,heat);point(out,b,x,y,flicker>.94?0x2727:flicker>.65?0x2219:0xb7,alpha,heat);
        }
        for(uint32_t j=0;j<12;j++){
            double a=j*30+randomAt(seed,j)*.2*180/NR_PI,r=b->speed*t*.7;
            segment(out,b,nrCos(a)*r*.15,nrSin(a)*r*.075,nrCos(a)*r,nrSin(a)*r*.5,decay(t*5)*.75,1);
        }
        if(age<450)point(out,b,0,0,age<90?0x2736:age<180?0x2739:0x2727,decay(age/220),1);
        if(age>180&&b->shockwave>0)glow(out,b->speed*t*1.1,fade*b->shockwave*b->intensity,.6,1);return 1;
    }
    for(uint32_t j=0;j<b->count;j++){
        double r=randomAt(seed,j*5),r2=randomAt(seed,j*5+1),q=randomAt(seed,j*5+2),glint=randomAt(seed+j,(uint32_t)nrFloor(t*b->glitterHz));
        double x=0,y=0,heat=.8;uint32_t glyph=0xb7;
        if(kind==2){
            double pos[2];ember(b,r,r2,t,pos);x=pos[0];y=pos[1];heat=.25+.55*(1-p);glyph=glint>.9?0x2727:glint>.5?0x2219:0xb7;
            if(b->trailMs){double prev[2];ember(b,r,r2,nrClamp(t-b->trailMs/1000,0,1e12),prev);segment(out,b,prev[0],prev[1],x,y,fade*.3,heat);}
        }else if(kind==3){x=(r-.5)*24+b->turbulence*t;y=-r2*18+t*b->speed;glyph=j%3?0x2571:0x2502;heat=.7;}
        else if(kind==4){x=(r-.5)*32+nrSin((t*1.6+r2*2*NR_PI)*180/NR_PI)*b->turbulence*2;y=-r2*20+t*b->speed*.22;glyph=q>.5?0xb7:0x22c5;}
        else{x=nrCos(r*360)*t*b->speed*q;y=nrSin(r*360)*t*b->speed*q*.5;}
        point(out,b,x,y,glyph,fade*(kind==2?.25+.75*glint:.7),heat);
    }if(kind==5)glow(out,t*b->speed,fade*.35*b->intensity,.65,1);return 1;
}

int nrAtelierCenter(const State*s,int slot,double out[3]){
    if(!out||nrAtelierProfile(s,slot)<0||!s->atelierControls[slot].used)return 0;
    int width,height;nrSceneViewport(s,&width,&height);
    Projection p;nrProjection(s,width,height,&p);int visible=nrProject(&p,s->emitters[slot].position,&out[0],&out[1],&out[2]);
    if(visible){out[0]*=.5;out[1]*=.25;}return visible;
}
static void screenSegment(NrContext*c,double x,double y,double xx,double yy,uint32_t color,double alpha,int material,uint32_t index){
    const State*s=nrView(c);int steps=(int)nrFloor(nrAbs(xx-x)+nrAbs(yy-y))+1;
    int previousX=NR_LAYOUT_MIN,previousY=NR_LAYOUT_MIN;
    for(int i=0;i<=steps;i++){
        double u=(double)i/steps;int px=(int)nrFloor(x+(xx-x)*u),py=(int)nrFloor(y+(yy-y)*u);
        if(px==previousX&&py==previousY)continue;previousX=px;previousY=py;
        if(px>=0&&py>=0&&px<(int)s->width&&py<(int)s->height){uint32_t ink=color;if(material>=0&&material<NR_MATERIALS&&s->materialPatterns[material].used){double ignored;ink=nrPaintAt(s,material,s->timeUs,px*256,py*256,index,&ignored);}nrCellBackground(c,px,py,ink,alpha);}
    }
}
/* Original RC2 EffectPainter.local Atelier branch and 80x44 tile compositor.
 * Reserved mode zero retains the existing material/pattern interpretation. */
static uint32_t mix(uint32_t a,uint32_t b,double t){
 t=nrClamp(t,0,1);uint32_t out=0;
 for(int shift=0;shift<=16;shift+=8){double aa=(a>>shift)&255,bb=(b>>shift)&255;out|=(uint32_t)nrFloor(aa*(1-t)+bb*t+.5)<<shift;}return out;
}
static uint32_t flattened(const uint32_t*c){return c[0]==0x2580||c[0]==0x2584||c[0]==0x258c||c[0]==0x2590?mix(c[1],c[2],.5):c[2];}
typedef struct {uint32_t width,height,*cells;const uint32_t*wheel;} Painter;
static uint32_t ink(const Painter*p,double hue){int h=(int)nrFloor(hue+.5)%360;if(h<0)h+=360;return p->wheel[h];}
static void cell(Painter*p,double x,double y,uint32_t glyph,uint32_t fg,double a){
 x=nrFloor(x);y=nrFloor(y);if(x<0||y<0||x>=p->width||y>=p->height)return;
 uint32_t*c=p->cells+4*((size_t)y*p->width+(size_t)x),bg=flattened(c);c[0]=glyph;c[1]=mix(bg,fg,a);c[2]=bg;c[3]=0;
}
static void dot(Painter*p,double x,double y,uint32_t color,double a){
 static const uint32_t bits[8]={1,8,2,16,4,32,64,128};x=nrFloor(x+.5);y=nrFloor(y+.5);
 if(x<0||y<0||x>=p->width*2.0||y>=p->height*4.0)return;
 uint64_t px=(uint64_t)x,py=(uint64_t)y;uint32_t*c=p->cells+4*((size_t)(py/4)*p->width+(size_t)(px/2));
 if(c[0]<0x2800||c[0]>0x28ff){c[2]=flattened(c);c[0]=0x2800;}
 c[0]|=bits[(py%4)*2+px%2];c[1]=mix(c[2],color,a);
}
static void line(Painter*p,double x0,double y0,double x1,double y1,uint32_t color,double a){
 x0*=2;x1*=2;y0*=4;y1*=4;double dx=x1-x0,dy=y1-y0,lo=0,hi=1;
 double ps[4]={-dx,dx,-dy,dy},qs[4]={x0,p->width*2.0-1-x0,y0,p->height*4.0-1-y0};
 for(int i=0;i<4;i++){double pp=ps[i],q=qs[i];if(!pp&&q<0)return;if(!pp)continue;double v=q/pp;if(pp<0){if(v>lo)lo=v;}else if(v<hi)hi=v;if(lo>hi)return;}
 double ax=nrFloor(x0+lo*dx+.5),ay=nrFloor(y0+lo*dy+.5),bx=nrFloor(x0+hi*dx+.5),by=nrFloor(y0+hi*dy+.5);
 double n=nrAbs(bx-ax);if(n<nrAbs(by-ay))n=nrAbs(by-ay);if(n<1)n=1;
 for(uint64_t j=0;j<=(uint64_t)n;j++)dot(p,ax+(bx-ax)*j/n,ay+(by-ay)*j/n,color,a);
}

static void sourcePaint(NrContext*c,const AtelierSample*sample,const double center[3],double weight){
    if(weight<=0)return;
    const State*s=nrView(c);uint32_t wheel[360],tile[80*44*4];
    for(int h=0;h<360;h++)if(nrWindowPaletteSourceTextInk(.83,.1,h,&wheel[h]))return;
    memset(tile,0,sizeof(tile));for(int i=0;i<80*44;i++)tile[i*4]=32;
    Painter p={80,44,tile,wheel};
    for(uint32_t i=0;i<sample->segmentCount;i++){
        const double*r=sample->segments[i];line(&p,40+r[0],22+r[1],40+r[2],22+r[3],ink(&p,30+r[5]*70),r[4]);
    }
    for(uint32_t i=0;i<sample->glowCount;i++){
        const double*r=sample->glows[i];double cx=40+r[0],cy=22+r[1],radius=r[2];
        int top=(int)nrClamp(nrFloor(cy-radius),0,44),left=(int)nrClamp(nrFloor(cx-radius*2),0,80);
        double bottom=nrClamp(cy+radius+1,0,44),right=nrClamp(cx+radius*2+1,0,80);
        for(int y=top;y<bottom;y++)for(int x=left;x<right;x++){
            double dx=x-cx,dy=(y-cy)*2,d=nrSqrt(dx*dx+dy*dy);
            double a=(r[5]?nrClamp(1-nrAbs(d-radius)/1.2,0,1):nrClamp(1-d/(radius*2>.2?radius*2:.2),0,1))*r[3];
            if(a>.004){uint32_t*cell=tile+4*(y*80+x);cell[2]=mix(cell[2],ink(&p,40+r[4]*30),a);}
        }
    }
    for(uint32_t i=0;i<sample->pointCount;i++){
        const double*r=sample->points[i];cell(&p,40+r[0],22+r[1],(uint32_t)r[2],ink(&p,35+r[4]*75),r[3]);
    }
    Painter dest={s->width,s->height,(uint32_t*)c->cells,wheel};
    for(int y=0;y<44;y++)for(int x=0;x<80;x++){
        const uint32_t*r=tile+4*(y*80+x);uint32_t g=r[0],fg=r[1],bg=r[2];
        if(!bg&&(g==32||!fg))continue;
        double xx=nrFloor(center[0]+x-40+.5),yy=nrFloor(center[1]+y-22+.5);
        if(xx<0||yy<0||xx>=s->width||yy>=s->height)continue;
        uint32_t*d=dest.cells+4*((size_t)yy*s->width+(size_t)xx);
        if(bg)d[2]=mix(flattened(d),bg,.7*weight);
        if(g!=32&&fg)cell(&dest,xx,yy,g,fg,.95*weight);
    }
}

void nrDrawAtelier(NrContext*c,const Projection*projection){
    const State*s=nrView(c);
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        if(!s->atelierControls[slot].used)continue;
        AtelierSample sample;double center[3];
        if(!nrAtelierSample(s,slot,&sample)||!nrProject(projection,s->emitters[slot].position,&center[0],&center[1],&center[2]))continue;
        center[0]*=.5;center[1]*=.25;const Emitter*e=&s->emitters[slot];double materialAlpha;
        nrUseMaterial(c,e->material);c->characterOwner=0;
        uint32_t color=nrPaint(s,e->material,s->timeUs,(uint32_t)e->id,&materialAlpha);double alpha=e->alpha*materialAlpha;
        if(s->atelierControls[slot].reserved){sourcePaint(c,&sample,center,alpha);continue;}
        for(uint32_t i=0;i<sample.glowCount;i++){
            const double*r=sample.glows[i];double cx=center[0]+r[0],cy=center[1]+r[1],radius=r[2],extent=radius+3;
            int left=(int)nrFloor(nrClamp(cx-extent,0,s->width)),right=(int)nrClamp(cx+extent+1,0,s->width);
            int top=(int)nrFloor(nrClamp(cy-extent*.5,0,s->height)),bottom=(int)nrClamp(cy+extent*.5+1,0,s->height);
            for(int y=top;y<bottom;y++)for(int x=left;x<right;x++){
                double dx=x+.5-cx,dy=2*(y+.5-cy),distance=nrSqrt(dx*dx+dy*dy);
                double envelope=r[5]?decay((distance-radius)*(distance-radius)):decay(distance*distance/(2*(radius*radius>.01?radius*radius:.01)));
                uint32_t ink=color;if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,x*256,y*256,i,&ignored);}nrCellBackground(c,x,y,ink,r[3]*envelope*alpha);
            }
        }
        for(uint32_t i=0;i<sample.segmentCount;i++){
            const double*r=sample.segments[i];screenSegment(c,center[0]+r[0],center[1]+r[1],center[0]+r[2],center[1]+r[3],color,r[4]*alpha,e->material,i);
        }
        /* Original source appends the nova core point last: preserve its layering. */
        for(uint32_t i=0;i<sample.pointCount;i++){
            const double*r=sample.points[i];double x=nrFloor(center[0]+r[0]),y=nrFloor(center[1]+r[1]);
            if(x>=0&&y>=0&&x<s->width&&y<s->height){uint32_t ink=color;if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,(int32_t)x*256,(int32_t)y*256,i,&ignored);}nrIndexedGlyph(c,(int)x,(int)y,(uint32_t)r[2],ink,r[3]*alpha,0,i);}
        }
    }c->paintBlend=0;
}
