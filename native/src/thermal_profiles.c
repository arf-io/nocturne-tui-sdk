#include "internal.h"
#include "window_palette_source.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
int nrThermalSourceProfile(const State*s,int slot){
    if(slot<0||slot>=(int)NR_MAX_EMITTERS||!s->emitters[slot].used)return -1;
    const char*name=nrEffectName(s->emitters[slot].effect);
    if(!strcmp(name,"weather/thermal-cinders"))return 0;
    if(!strcmp(name,"weather/autumn-drift"))return 1;return -1;
}
static int valid(const ThermalSourceControls*b){return b->used==1&&b->reserved<=1&&b->lifeMs>=200&&b->lifeMs<=10000;}
int nrValidThermalSourceControls(const State*s){
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        const ThermalSourceControls*b=&s->thermalSourceControls[slot];
        if(!b->used){const unsigned char*p=(const unsigned char*)b;for(size_t i=0;i<sizeof(*b);i++)if(p[i])return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_THERMAL_PROFILES||(b->reserved&&s->schema<NR_STATE_SCHEMA_THERMAL_PAINT)||nrThermalSourceProfile(s,slot)<0||!valid(b)||b->generation!=s->emitters[slot].generation||b->startUs>s->timeUs)return 0;
    }return 1;
}
int nrThermalSourceCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_THERMAL_PROFILES)return reject(c,"Thermal source requires schema61");
    int removal=nrEqual(j,nrField(j,0,"op"),"remove-thermal-style");double id;
    if(!nrAllowed(j,0,removal?"op id":"op id seed lifeMs paint"))return reject(c,"Unknown thermal source setting");
    if(!nrNumber(j,nrField(j,0,"id"),&id)||id<1||id>65535||id!=(uint32_t)id)return reject(c,"Thermal source emitter id required");
    int slot=nrFindEmitter(s,(int)id);if(nrThermalSourceProfile(s,slot)<0)return reject(c,"Thermal source requires thermal ember or leaf emitter");
    if(removal){memset(&s->thermalSourceControls[slot],0,sizeof(ThermalSourceControls));return 0;}
    ThermalSourceControls b=s->thermalSourceControls[slot];if(!b.used)b=(ThermalSourceControls){.used=1,.reserved=1,.generation=s->emitters[slot].generation,.seed=2030,.lifeMs=6500,.startUs=s->timeUs};
    int mode=nrField(j,0,"paint");if(mode>=0){if(nrEqual(j,mode,"source"))b.reserved=1;else if(nrEqual(j,mode,"material"))b.reserved=0;else return reject(c,"Invalid thermal painting mode");}
    if(b.reserved&&s->schema<NR_STATE_SCHEMA_THERMAL_PAINT)return reject(c,"Thermal painting requires schema79");
    int at=nrField(j,0,"seed");double value;
    if(at>=0){if(!nrNumber(j,at,&value)||value<0||value>4294967295.0||value!=(uint32_t)value)return reject(c,"Thermal seed requires uint32");b.seed=(uint32_t)value;}
    at=nrField(j,0,"lifeMs");if(at>=0){if(!nrNumber(j,at,&value)||value<200||value>10000)return reject(c,"Thermal lifeMs out of range");b.lifeMs=value;}
    if(!valid(&b))return reject(c,"Invalid thermal source controls");s->thermalSourceControls[slot]=b;return 0;
}
static double randomAt(uint32_t seed,uint32_t index){return nrHash(seed^((index+1u)*2654435769u))/4294967296.0;}
static double power16(double x){
    if(x<=0)return 0;if(x>=1)return 1;int exponent=0;while(x<.75){x*=2;exponent--;}
    double z=(x-1)/(x+1),square=z*z,term=z,sum=z;for(int i=3;i<=39;i+=2){term*=square;sum+=term/i;}
    double arg=-1.6*(2*sum+exponent*.6931471805599453094);int squares=0;while(arg>.125){arg*=.5;squares++;}
    double result=1;term=1;for(int i=1;i<=20;i++){term*=-arg/i;result+=term;}for(int i=0;i<squares;i++)result*=result;return result;
}
static double sine(double radians){return nrSin(radians*180/NR_PI);}
static double cosine(double radians){return nrCos(radians*180/NR_PI);}
static Vec3 emberAt(uint32_t seed,uint32_t i,double t){
    double rise=.5+randomAt(seed,i*11)*.45,H=8+randomAt(seed,i*11+1)*13,fall=2.9+randomAt(seed,i*11+2)*1.6;
    double u=1-t/rise,y=t<rise?H*(1-u*u):H*(1-power16(nrClamp((t-rise)/fall,0,1)));
    double drift=(randomAt(seed,i*11+3)-.5)*4,swirl=randomAt(seed,i*11+4)*2*NR_PI;
    return nrV(drift*t*.55+sine(t*2.3+swirl)*(t*.6<2?t*.6:2),y>0?y:0,(randomAt(seed,i*11+5)-.5)*t*2+cosine(t+swirl)*t*.2);
}
static void segment(ThermalSourceSample*out,Vec3 a,Vec3 b,double opacity,double hue){
    if(out->segmentCount>=400)return;double*r=out->segments[out->segmentCount++];r[0]=a.x;r[1]=a.y;r[2]=a.z;r[3]=b.x;r[4]=b.y;r[5]=b.z;r[6]=opacity;r[7]=hue;
}
static Vec3 leafVertex(Vec3 center,double scale,double ca,double sa,double cr,double sr,double x,double y){
    double u=(x*sa+y*ca)*scale;return nrV(center.x+(x*ca-y*sa)*scale,center.y+u*cr,center.z+u*sr);
}
int nrThermalSourceSample(const State*s,int slot,ThermalSourceSample*out){
    int kind=nrThermalSourceProfile(s,slot);if(!out||kind<0||!s->thermalSourceControls[slot].used)return 0;
    const ThermalSourceControls*b=&s->thermalSourceControls[slot];if(b->generation!=s->emitters[slot].generation)return 0;
    memset(out,0,sizeof(*out));double age=(double)(s->timeUs-b->startUs)/1000;if(age>=b->lifeMs)return 1;
    double t=age/1000;uint32_t seed=b->seed;
    if(kind==0){
        for(uint32_t i=0;i<88;i++){
            double tt=t-randomAt(seed,i*11+6)*.23;if(tt<0)continue;
            int survivor=randomAt(seed,i*11+7)<.12;double burnout=survivor?b->lifeMs/1000:1.25+randomAt(seed,i*11+8)*3.1;if(tt>burnout)continue;
            Vec3 p=emberAt(seed,i,tt);int ground=p.y<.02;double fade=nrClamp((burnout-tt)/.65,0,1),flicker=.5+.5*randomAt(seed+i,(uint32_t)nrFloor(tt*12));
            double alpha=fade*flicker*(ground?.35:nrClamp(1-tt*.075,.3,1)),heat=nrClamp(1-tt/6,0,1);
            double*r=out->points[out->pointCount++];r[0]=p.x;r[1]=p.y;r[2]=p.z;r[3]=ground?0xb7:flicker>.92?0x2727:flicker>.75?0x2219:0xb7;r[4]=alpha;r[5]=18+heat*38;
            if(!ground)segment(out,emberAt(seed,i,tt>.055?tt-.055:0),p,alpha*.45,28+heat*30);
        }
    }else{
        for(uint32_t i=0;i<20;i++){
            double tt=t-randomAt(seed,i*9)*.45;if(tt<0)continue;
            double phase=randomAt(seed,i*9+1)*2*NR_PI,h=12+randomAt(seed,i*9+2)*10,scale=1.1+randomAt(seed,i*9+3)*1.1;
            double y=h-tt*(2.8+randomAt(seed,i*9+5));Vec3 center=nrV((randomAt(seed,i*9+4)-.5)*28+tt*1.5+sine(tt*1.7+phase)*2,y>0?y:0,(randomAt(seed,i*9+6)-.5)*17+sine(tt*.8+phase)*3);
            double yaw=phase+tt*(.7+randomAt(seed,i*9+7)),roll=sine(tt*2+phase)*1.15,ca=cosine(yaw),sa=sine(yaw),cr=cosine(roll),sr=sine(roll);
            double alpha=nrClamp((b->lifeMs/1000-tt)/1.1,0,1)*(center.y<.1?.65:1),hue=28+randomAt(seed,i*9+8)*60;Vec3 previous=nrV(0,0,0);
            for(int k=0;k<17;k++){double a=k*2*NR_PI/16;Vec3 v=leafVertex(center,scale,ca,sa,cr,sr,sine(a)*.48*sine(a/2),cosine(a));if(k)segment(out,previous,v,alpha*.85,hue);previous=v;}
            segment(out,leafVertex(center,scale,ca,sa,cr,sr,0,-1.25),leafVertex(center,scale,ca,sa,cr,sr,0,.85),alpha*.9,hue+12);
            const double veins[]={-.4,.15,.6};for(int k=0;k<3;k++)segment(out,leafVertex(center,scale,ca,sa,cr,sr,0,veins[k]-.2),leafVertex(center,scale,ca,sa,cr,sr,.3,veins[k]+.05),alpha*.45,hue+6);
        }
    }return 1;
}
/* Clip in world depth before division. The same helper serves metadata and paint. */
int nrThermalSourceProjectSegment(const Projection*p,Vec3 origin,const double*r,double out[6]){
    Vec3 a=nrAdd(origin,nrV(r[0],r[1],r[2])),b=nrAdd(origin,nrV(r[3],r[4],r[5]));
    double za=nrDot(nrSub(a,p->position),p->forward),zb=nrDot(nrSub(b,p->position),p->forward),low=0,high=1;
    if(za==zb){if(za<p->nearPlane||za>p->farPlane)return 0;}
    else{
        double t0=(p->nearPlane-za)/(zb-za),t1=(p->farPlane-za)/(zb-za);
        if(t0>t1){double tmp=t0;t0=t1;t1=tmp;}if(t0>low)low=t0;if(t1<high)high=t1;if(low>high)return 0;
    }
    Vec3 d=nrSub(b,a),aa=nrAdd(a,nrScale(d,low)),bb=nrAdd(a,nrScale(d,high));
    /* Clipped depths are analytically valid; avoid rejecting boundary roundoff. */
    const Vec3 v[]={aa,bb};for(int i=0;i<2;i++){
        Vec3 relative=nrSub(v[i],p->position);double z=nrClamp(nrDot(relative,p->forward),p->nearPlane,p->farPlane),f=p->orthographic?p->scale:p->focal/z;
        out[i*3]=(p->cx+nrDot(relative,p->right)*f)*.5;out[i*3+1]=(p->cy-nrDot(relative,p->up)*f)*.25;out[i*3+2]=z;
    }return 1;
}
uint32_t nrSourcePrimitiveColor(uint32_t material,double hue){
    /* Source hue replaces material hue, retaining its lightness/chroma. An
     * achromatic material uses the source's fixed OKLCH(.78,.14) palette. */
    if(((material>>16)&255)==((material>>8)&255)&&((material>>8)&255)==(material&255))return nrLabColor(.78,.14*nrCos(hue),.14*nrSin(hue));
    return nrColorWithHue(material,hue);
}
void nrSourceScreenSegment(NrContext*c,const double*r,uint32_t color,double alpha,int material,uint32_t index){
    const State*s=nrView(c);double dx=r[3]-r[0],dy=r[4]-r[1],low=0,high=1;
    /* Liang-Barsky terminal rectangle clipping bounds work for near-plane spans. */
    const double p[]={-dx,dx,-dy,dy},q[]={r[0],(double)s->width-r[0],r[1],(double)s->height-r[1]};
    for(int k=0;k<4;k++){if(p[k]==0){if(q[k]<0)return;}else{double t=q[k]/p[k];if(p[k]<0){if(t>high)return;if(t>low)low=t;}else{if(t<low)return;if(t<high)high=t;}}}
    double x=r[0]+dx*low,y=r[1]+dy*low,xx=r[0]+dx*high,yy=r[1]+dy*high;
    int steps=(int)nrFloor(nrAbs(xx-x)+nrAbs(yy-y))+1,previousX=NR_LAYOUT_MIN,previousY=NR_LAYOUT_MIN;
    for(int i=0;i<=steps;i++){double u=(double)i/steps;int px=(int)nrFloor(x+(xx-x)*u),py=(int)nrFloor(y+(yy-y)*u);
        if(px==previousX&&py==previousY)continue;previousX=px;previousY=py;
        if(px>=0&&py>=0&&px<(int)s->width&&py<(int)s->height){uint32_t ink=color;if(material>=0&&material<NR_MATERIALS&&s->materialPatterns[material].used){double ignored;ink=nrPaintAt(s,material,s->timeUs,px*256,py*256,index,&ignored);}nrCellBackground(c,px,py,ink,alpha);}
    }
}
/* The original world is +Z-forward. Map its local geometry once into
 * the canonical native -Z-forward world, keeping emitter origin native. */
static int originalPoint(const Projection*p,Vec3 origin,const double*r,double out[3]){
    if(!nrProject(p,nrV(origin.x+r[0],origin.y+r[1],origin.z-r[2]),&out[0],&out[1],&out[2]))return 0;
    out[0]*=.5;out[1]*=.25;return 1;
}
int nrThermalOriginalProjectSegment(const Projection*p,Vec3 origin,const double*r,double out[6]){
    /* Actual EffectPainter.thermal draws only when both original endpoints
     * project; the previous clipped-segment policy remains in material mode. */
    return originalPoint(p,origin,r,out)&&originalPoint(p,origin,r+3,out+3);
}
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

static void originalPaint(NrContext*c,const State*s,int slot,const Projection*projection,const ThermalSourceSample*sample,double weight){
    if(weight<=0)return;uint32_t wheel[360];for(int h=0;h<360;h++)if(nrWindowPaletteSourceTextInk(.83,.1,h,&wheel[h]))return;
    Painter p={s->width,s->height,(uint32_t*)c->cells,wheel};Vec3 origin=s->emitters[slot].position;
    for(uint32_t i=0;i<sample->segmentCount;i++){
        const double*r=sample->segments[i];double q[6];if(nrThermalOriginalProjectSegment(projection,origin,r,q))line(&p,q[0],q[1],q[3],q[4],ink(&p,r[7]),r[6]*weight);
    }
    for(uint32_t i=0;i<sample->pointCount;i++){
        const double*r=sample->points[i];double q[3];if(originalPoint(projection,origin,r,q))cell(&p,q[0],q[1],(uint32_t)r[3],ink(&p,r[5]),r[4]*weight);
    }
}

void nrDrawThermalSource(NrContext*c,const Projection*p){
    const State*s=nrView(c);
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        if(!s->thermalSourceControls[slot].used)continue;ThermalSourceSample sample;if(!nrThermalSourceSample(s,slot,&sample))continue;
        const Emitter*e=&s->emitters[slot];nrUseMaterial(c,e->material);c->characterOwner=0;double materialAlpha;
        uint32_t material=nrPaint(s,e->material,s->timeUs,(uint32_t)e->id,&materialAlpha);double alpha=e->alpha*materialAlpha;
        if(s->thermalSourceControls[slot].reserved){originalPaint(c,s,slot,p,&sample,alpha);continue;}
        for(uint32_t i=0;i<sample.segmentCount;i++){const double*r=sample.segments[i];double projected[6];
            if(nrThermalSourceProjectSegment(p,e->position,r,projected))nrSourceScreenSegment(c,projected,nrSourcePrimitiveColor(material,r[7]),alpha*r[6],e->material,i);}
        for(uint32_t i=0;i<sample.pointCount;i++){const double*r=sample.points[i];Vec3 v=nrAdd(e->position,nrV(r[0],r[1],r[2]));double x,y,z;
            if(!nrProject(p,v,&x,&y,&z))continue;x=nrFloor(x*.5);y=nrFloor(y*.25);
            if(x>=0&&y>=0&&x<s->width&&y<s->height){uint32_t ink=nrSourcePrimitiveColor(material,r[5]);if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,(int32_t)x*256,(int32_t)y*256,i,&ignored);}nrIndexedGlyph(c,(int)x,(int)y,(uint32_t)r[3],ink,alpha*r[4],0,i);}
        }
    }c->paintBlend=0;
}
