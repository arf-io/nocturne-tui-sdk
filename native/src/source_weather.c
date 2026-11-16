#include "source_weather.h"
#include <stddef.h>
#include <string.h>
#include <limits.h>

extern double nrClamp(double,double,double);
extern double nrFloor(double);
extern double nrSqrt(double);
extern double nrPowPositive(double,double);
extern double nrAbs(double);
extern uint32_t nrHash(uint32_t);
#define NR_PI 3.14159265358979323846
#include "window_source_math.h"

/* Direct current-C port of the pinned RC2 Kinetic sampler and cell painter.
 * All clocks and random indices remain the original event's, not a generated
 * particle ID or the SDK presentation clock. Original JS executes only in tests. */
static int bounded(double v,double lo,double hi){return v>=lo&&v<=hi;}
static uint32_t uint32Number(double v){v-=4294967296.0*nrFloor(v/4294967296.0);return (uint32_t)v;}
static double randomAt(uint32_t seed,uint32_t index,double salt){
 return nrHash(seed^uint32Number(salt*2246822519.0)^((index+1)*0x9e3779b9u))/4294967296.0;
}
static double expNegative(double x){
 if(x>745)return 0;
 int squares=0;while(x>.125){x*=.5;squares++;}
 double value=1,term=1;for(int i=1;i<=20;i++){term*= -x/i;value+=term;}
 while(squares--)value*=value;return value;
}
void nrSourceWeatherDefaults(NrSourceWeatherOptions *o){
 if(!o)return;
 *o=(NrSourceWeatherOptions){.count=52,.lifeMs=5000,.launchSpeed=12,.gravity=8,.drag=.65,
 .wind=1.2,.flickerHz=18,.trailMs=90,.branches=5,.arcSegments=10,.arcJitter=1.2,.coreMs=260,
 .shockwave=0,.explosionForce=48,.seed=2030,.brightness=.85,.emberSpread=5,.arcReach=17,
 .glyphCount=8,.glyphs={0xb7,0x2219,0x22c5,'*','+',0x2801,0x2802,0x2804}};
}
int nrSourceWeatherValidate(const NrSourceWeatherOptions *o){
 if(!o)return 0;
#define CHECK(k,lo,hi) if(!bounded(o->k,lo,hi))return 0
 CHECK(count,1,160);CHECK(lifeMs,100,12000);CHECK(launchSpeed,0,40);CHECK(gravity,0,40);
 CHECK(drag,0,5);CHECK(wind,-20,20);CHECK(flickerHz,0,60);CHECK(trailMs,0,400);
 CHECK(branches,1,12);CHECK(arcSegments,3,24);CHECK(arcJitter,0,6);CHECK(coreMs,0,1500);
 CHECK(shockwave,0,1);CHECK(explosionForce,1,70);CHECK(seed,0,4294967295.0);
 CHECK(brightness,0,1);CHECK(emberSpread,0,20);CHECK(arcReach,1,45);
#undef CHECK
 if(o->count!=nrFloor(o->count)||o->branches!=nrFloor(o->branches)||o->arcSegments!=nrFloor(o->arcSegments)||o->seed!=nrFloor(o->seed)||!o->glyphCount||o->glyphCount>64)return 0;
 for(uint32_t i=0;i<o->glyphCount;i++){uint32_t g=o->glyphs[i];if(g<32||(g>=127&&g<=159)||(g>=0xd800&&g<=0xdfff)||g>0x10ffff)return 0;}
 return 1;
}
static int validEvent(const NrSourceWeatherEvent *e,double t){
 return e&&e->kind<=NR_SOURCE_WEATHER_RIPPLES&&bounded(e->id,0,9007199254740991.0)&&bounded(e->atMs,0,9007199254740991.0)&&bounded(t,0,9007199254740991.0)&&bounded(e->x,-100000,100000)&&bounded(e->y,-100000,100000);
}
static void point(NrSourceWeatherSample*r,const NrSourceWeatherEvent*e,double x,double y,double a,double heat,uint32_t glyph){
 r->points[r->pointCount++]=(NrSourceWeatherPoint){e->x+x,e->y+y,nrClamp(a,0,1),heat,1,glyph};
}
static void segment(NrSourceWeatherSample*r,const NrSourceWeatherEvent*e,double x1,double y1,double x2,double y2,double a,double heat,uint32_t branch){
 r->segments[r->segmentCount++]=(NrSourceWeatherSegment){e->x+x1,e->y+y1,e->x+x2,e->y+y2,nrClamp(a,0,1),heat,branch};
}
static NrSourceWeatherPoint ember(uint32_t i,double age,uint32_t seed,const NrSourceWeatherOptions*o){
 double t=(age<0?0:age)/1000,vy=o->launchSpeed*(.72+.55*randomAt(seed,i,11)),vx=(randomAt(seed,i,12)-.5)*o->emberSpread;
 double d=o->drag?(1-expNegative(o->drag*t))/o->drag:t;
 double x=vx*d+o->wind*t+.4*nrWindowSourceSin(t*3+randomAt(seed,i,13)*6)*t;
 double y=-vy*t+.5*o->gravity*t*t,life=o->lifeMs*(.9+.1*randomAt(seed,i,14)),fade=nrClamp(1-age/life,0,1);
 double flicker=.35+.65*randomAt(seed,i,nrFloor(age*o->flickerHz/1000)+201);
 return (NrSourceWeatherPoint){x,y,nrPowPositive(fade,.65)*flicker*o->brightness,.1+.4*fade,1,o->glyphs[(uint32_t)nrFloor(randomAt(seed,i,16)*o->glyphCount)]};
}
int nrSourceWeatherSample(const NrSourceWeatherEvent*e,double timeMs,const NrSourceWeatherOptions*o,NrSourceWeatherSample*out){
 if(!out||!validEvent(e,timeMs)||!nrSourceWeatherValidate(o))return -1;
 NrSourceWeatherSample r;memset(&r,0,sizeof(r));double age=timeMs-e->atMs,t=age/1000;
 if(age<0||age>=o->lifeMs){*out=r;return 0;}
 uint32_t seed=(uint32_t)o->seed^uint32Number(e->id*2654435761.0),count=(uint32_t)o->count;
 double remaining=1-age/o->lifeMs,fade=nrPowPositive(remaining,1.5);
 if(e->kind==NR_SOURCE_WEATHER_EMBERS){
  for(uint32_t i=0;i<count;i++){
   double a=age-randomAt(seed,i,9)*180;if(a<0)continue;
   NrSourceWeatherPoint p=ember(i,a,seed,o);point(&r,e,p.x,p.y,p.opacity,p.heat,p.glyph);
   if(o->trailMs&&p.opacity>.02){NrSourceWeatherPoint q=ember(i,a>o->trailMs?a-o->trailMs:0,seed,o);segment(&r,e,q.x,q.y,p.x,p.y,p.opacity*.25,p.heat,0);}
  }
 }else if(e->kind==NR_SOURCE_WEATHER_SPARKS){
  double envelope=expNegative(age/(o->lifeMs*.22>100?o->lifeMs*.22:100));
  double flicker=.45+.55*randomAt(seed,(uint32_t)nrFloor(age*(o->flickerHz>1?o->flickerHz:1)/1000),43);
  r.core=expNegative(age/(o->coreMs>1?o->coreMs:1))*.65*o->brightness;
  for(uint32_t b=0;b<(uint32_t)o->branches;b++){
   double angle=randomAt(seed,b,44)*NR_PI*2;
   double reach=o->arcReach*(.5+.5*randomAt(seed,b,45))*(.4+.6*(age/90<1?age/90:1)),x=0,y=0;
   for(uint32_t j=1;j<=(uint32_t)o->arcSegments;j++){
    double u=j/o->arcSegments,jit=(randomAt(seed,b*37+j,nrFloor(age*(o->flickerHz>1?o->flickerHz:1)/1000)+51)-.5)*o->arcJitter;
    double nx=nrWindowSourceCos(angle)*reach*u-nrWindowSourceSin(angle)*jit,ny=(nrWindowSourceSin(angle)*reach*u+nrWindowSourceCos(angle)*jit)*.5;
    segment(&r,e,x,y,nx,ny,envelope*flicker*o->brightness,.85,b);
    if(j%3==0){double a2=angle+(randomAt(seed,j,b+71)-.5)*2.3,len=reach*.23;
     segment(&r,e,nx,ny,nx+nrWindowSourceCos(a2)*len,ny+nrWindowSourceSin(a2)*len*.5,envelope*.65*o->brightness,1,b+1);
     point(&r,e,nx,ny,envelope*flicker*o->brightness,1,'*');}
    x=nx;y=ny;
   }
  }
  for(uint32_t i=0;i<count&&i<40;i++){double a=randomAt(seed,i,84)*NR_PI*2,v=o->explosionForce*(.3+.7*randomAt(seed,i,85));
   point(&r,e,nrWindowSourceCos(a)*v*t,nrWindowSourceSin(a)*v*t*.5+.6*t*t,fade*expNegative(t*2)*o->brightness,.75,o->glyphs[i%o->glyphCount]);}
 }else if(e->kind==NR_SOURCE_WEATHER_NOVA){
  r.core=o->coreMs?nrSqrt(nrClamp(1-age/o->coreMs,0,1))*o->brightness:0;r.radius=o->explosionForce*t;r.shockwave=o->shockwave*fade;
  for(uint32_t i=0;i<count;i++){
   double a=randomAt(seed,i,91)*NR_PI*2,v=o->explosionForce*(.3+.9*randomAt(seed,i,92)),d=o->drag?(1-expNegative(o->drag*t))/o->drag:t;
   double x=nrWindowSourceCos(a)*v*d,y=nrWindowSourceSin(a)*v*d*.5,exposure=t-o->trailMs/1000;if(exposure<0)exposure=0;
   double previous=o->drag?(1-expNegative(o->drag*exposure))/o->drag:exposure;
   double flicker=.4+.6*randomAt(seed,i,nrFloor(age*o->flickerHz/1000)+100),a0=fade*flicker*o->brightness;
   point(&r,e,x,y,a0,.3+.7*fade,age<150?'*':o->glyphs[i%o->glyphCount]);
   segment(&r,e,nrWindowSourceCos(a)*v*previous,nrWindowSourceSin(a)*v*previous*.5,x,y,a0*.9,.7,0);
   if(age<o->coreMs*2&&i<20)segment(&r,e,x*.15,y*.15,x*1.4,y*1.4,expNegative(age/180)*o->brightness,.95,0);
  }
 }else if(e->kind==NR_SOURCE_WEATHER_RAIN||e->kind==NR_SOURCE_WEATHER_SNOW){
  for(uint32_t i=0;i<count;i++){
   double delay=randomAt(seed,i,120)*o->lifeMs*.6,lt=(age-delay)/1000;if(lt<0)continue;
   double v=o->launchSpeed*(.4+randomAt(seed,i,121));
   double x=(randomAt(seed,i,122)-.5)*24+o->wind*lt+(e->kind==NR_SOURCE_WEATHER_SNOW?nrWindowSourceSin(lt*2+i)*1.7:0),y=-8+v*lt;
   point(&r,e,x,y,fade*o->brightness,.6,e->kind==NR_SOURCE_WEATHER_SNOW?0xb7:0x2502);
  }
 }else{r.radius=o->explosionForce*t;r.shockwave=fade*o->brightness;}
 *out=r;return 0;
}

static uint32_t mix(uint32_t a,uint32_t b,double t){
 t=nrClamp(t,0,1);uint32_t out=0;
 for(int shift=0;shift<=16;shift+=8){double aa=(a>>shift)&255,bb=(b>>shift)&255;out|=(uint32_t)nrFloor(aa*(1-t)+bb*t+.5)<<shift;}return out;
}
static uint32_t flattened(const uint32_t*c){return c[0]==0x2580||c[0]==0x2584||c[0]==0x258c||c[0]==0x2590?mix(c[1],c[2],.5):c[2];}
/* Writes land only inside the clip rectangle (cells [x0,x1) x [y0,y1)); geometry always uses the full
 * width and height, so a clipped paint writes exactly the cells an unclipped paint writes inside it. */
typedef struct {uint32_t width,height,*cells;const uint32_t*wheel;uint32_t x0,y0,x1,y1;} Painter;
static uint32_t ink(const Painter*p,double hue){int h=(int)nrFloor(hue+.5)%360;if(h<0)h+=360;return p->wheel[h];}
static void cell(Painter*p,double x,double y,uint32_t glyph,uint32_t fg,double a){
 x=nrFloor(x);y=nrFloor(y);if(x<p->x0||y<p->y0||x>=p->x1||y>=p->y1)return;
 uint32_t*c=p->cells+4*((size_t)y*p->width+(size_t)x),bg=flattened(c);c[0]=glyph;c[1]=mix(bg,fg,a);c[2]=bg;c[3]=0;
}
static void dot(Painter*p,double x,double y,uint32_t color,double a){
 static const uint32_t bits[8]={1,8,2,16,4,32,64,128};x=nrFloor(x+.5);y=nrFloor(y+.5);
 if(x<0||y<0||x>=p->width*2.0||y>=p->height*4.0)return;
 if(x<p->x0*2.0||y<p->y0*4.0||x>=p->x1*2.0||y>=p->y1*4.0)return;
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
static int paintClipped(const NrSourceWeatherEvent*e,double timeMs,const NrSourceWeatherOptions*o,double weight,const uint32_t wheel[360],uint32_t width,uint32_t height,uint32_t*cells,const uint32_t clip[4]){
 if(!cells||!wheel||!width||!height||!bounded(weight,0,1)||(uint64_t)width*height>SIZE_MAX/(4*sizeof(uint32_t)))return -1;
 for(int i=0;i<360;i++)if(wheel[i]>0xffffff)return -1;
 NrSourceWeatherSample r;if(nrSourceWeatherSample(e,timeMs,o,&r))return -1;
 if(!weight)return 0;Painter p={width,height,cells,wheel,clip[0],clip[1],clip[2],clip[3]};
 for(uint32_t i=0;i<r.segmentCount;i++){const NrSourceWeatherSegment*s=&r.segments[i];
  line(&p,s->x1,s->y1,s->x2,s->y2,ink(&p,e->kind==0?40+s->heat*35:e->kind==1?210+s->heat*80:285+s->heat*90),s->opacity*weight);}
 for(uint32_t i=0;i<r.pointCount;i++){const NrSourceWeatherPoint*q=&r.points[i];
  cell(&p,q->x,q->y,q->glyph,ink(&p,e->kind==0?35+q->heat*40:e->kind==1?215+q->heat*60:285+q->heat*85),q->opacity*weight);}
 if(r.core>.01){double radius=1+r.core*3;
  /* Clip bounds before iteration: excluded source iterations never wrote cells. */
  double top=nrFloor(e->y-radius),left=nrFloor(e->x-radius*2),bottom=e->y+radius,right=e->x+radius*2;
  if(top<clip[1])top=clip[1];if(left<clip[0])left=clip[0];if(bottom>=clip[3])bottom=clip[3]-1.0;if(right>=clip[2])right=clip[2]-1.0;
  for(int64_t y=(int64_t)top;y<=bottom;y++)for(int64_t x=(int64_t)left;x<=right;x++){
   double dx=x-e->x,dy=(y-e->y)*2,dist=nrSqrt(dx*dx+dy*dy),a=(1-dist/(radius*2));if(a<0)a=0;a*=r.core*weight;
   if(a>.02){uint32_t*c=cells+4*((size_t)y*width+(size_t)x),bg=flattened(c);c[2]=mix(bg,0xece2f4,a*.5);cell(&p,x,y,dist<1?0x2736:dist<3?0x2733:0x22c6,0xf2eaf3,a);}
  }
 }
 if(r.shockwave>.005)for(int j=0;j<96;j++){double a=j*NR_PI/48;dot(&p,(e->x+nrWindowSourceCos(a)*r.radius)*2,(e->y+nrWindowSourceSin(a)*r.radius*.5)*4,ink(&p,290),r.shockwave*weight);}
 return 0;
}
int nrSourceWeatherPaint(const NrSourceWeatherEvent*e,double timeMs,const NrSourceWeatherOptions*o,double weight,const uint32_t wheel[360],uint32_t width,uint32_t height,uint32_t*cells){
 const uint32_t clip[4]={0,0,width,height};return paintClipped(e,timeMs,o,weight,wheel,width,height,cells,clip);
}

int nrSourceWeatherPaintLayerClipped(const NrSourceWeatherEvent*events,uint32_t eventCount,
 double timeMs,const NrSourceWeatherOptions*o,double weatherIntensity,
 double novaStrength,double novaRegularity,const uint32_t wheel[360],
 uint32_t width,uint32_t height,uint32_t*cells,uint32_t clipX,uint32_t clipY,uint32_t clipWidth,uint32_t clipHeight){
 if(clipX>width||clipY>height||clipWidth>width-clipX||clipHeight>height-clipY)return -1;
 const uint32_t clip[4]={clipX,clipY,clipX+clipWidth,clipY+clipHeight};
 if((eventCount&&!events)||!bounded(timeMs,0,9007199254740991.0)||!nrSourceWeatherValidate(o)||
 !bounded(weatherIntensity,0,1)||!bounded(novaStrength,0,1)||!bounded(novaRegularity,0,60)||
 !cells||!wheel||!width||!height||(uint64_t)width*height>SIZE_MAX/(4*sizeof(uint32_t)))return -1;
 for(int i=0;i<360;i++)if(wheel[i]>0xffffff)return -1;
 for(uint32_t i=0;i<eventCount;i++)if(!validEvent(&events[i],timeMs))return -1;
 if(weatherIntensity==0)return 0;
 uint32_t chosen[24],count=0,first=0;
 for(uint32_t i=0;i<eventCount;i++)if(events[i].atMs<=timeMs&&timeMs-events[i].atMs<o->lifeMs){
  if(count<24)chosen[count++]=i;else{chosen[first]=i;first=(first+1)%24;}}
 NrSourceWeatherEvent automatic[2];uint32_t autoCount=0;
 if(novaRegularity){
  double period=60000/novaRegularity,k=nrFloor(timeMs/period),start=k-1;if(start<1)start=1;
  /* At most two events, including when k exceeds exact uint32 representation. */
  for(int offset=0;offset<2;offset++){
   double n=start+offset;if(n>k)break;
   if(timeMs-n*period<o->lifeMs){
    uint32_t index=uint32Number(n);
    double x=nrHash(53u^((index+1)*0x9e3779b9u))/4294967296.0*width;
    double y=5+nrHash(79u^((index+1)*0x9e3779b9u))/4294967296.0*(height-12.0);
    automatic[autoCount]=(NrSourceWeatherEvent){NR_SOURCE_WEATHER_NOVA,900000+n,x,y,n*period};
    if(!validEvent(&automatic[autoCount],timeMs))return -1;autoCount++;
   }
  }
 }
 /* Validate generated events too before painting any explicit event. */
 for(uint32_t k=0;k<count;k++){
  const NrSourceWeatherEvent*e=&events[chosen[(first+k)%24]];
  double weight=nrClamp(weatherIntensity*2.6*(e->kind==NR_SOURCE_WEATHER_NOVA?novaStrength:1),0,1);
  paintClipped(e,timeMs,o,weight,wheel,width,height,cells,clip);
 }
 for(uint32_t i=0;i<autoCount;i++)paintClipped(&automatic[i],timeMs,o,
  nrClamp(weatherIntensity*2.6*novaStrength,0,1),wheel,width,height,cells,clip);
 count+=autoCount;
 return (int)count;
}
int nrSourceWeatherPaintLayer(const NrSourceWeatherEvent*events,uint32_t eventCount,
 double timeMs,const NrSourceWeatherOptions*o,double weatherIntensity,
 double novaStrength,double novaRegularity,const uint32_t wheel[360],
 uint32_t width,uint32_t height,uint32_t*cells){
 return nrSourceWeatherPaintLayerClipped(events,eventCount,timeMs,o,weatherIntensity,novaStrength,novaRegularity,wheel,width,height,cells,0,0,width,height);
}

int nrSourceWeatherDrawSegment(double x0,double y0,double x1,double y1,uint32_t color,double alpha,uint32_t width,uint32_t height,uint32_t*cells){
 if(!cells||!width||!height||color>0xffffff||!bounded(alpha,0,1)||!bounded(x0,-1e12,1e12)||!bounded(x1,-1e12,1e12)||!bounded(y0,-1e12,1e12)||!bounded(y1,-1e12,1e12)||(uint64_t)width*height>SIZE_MAX/(4*sizeof(uint32_t)))return -1;
Painter p={width,height,cells,0,0,0,width,height};line(&p,x0,y0,x1,y1,color,alpha);return 0;
}

int nrSourcePaintCell(double x,double y,uint32_t glyph,uint32_t color,double alpha,uint32_t width,uint32_t height,uint32_t*cells){
 if(!cells||!width||!height||color>0xffffff||!bounded(alpha,0,1)||!bounded(x,-1e12,1e12)||!bounded(y,-1e12,1e12)||(uint64_t)width*height>SIZE_MAX/(4*sizeof(uint32_t)))return -1;
Painter p={width,height,cells,0,0,0,width,height};cell(&p,x,y,glyph,color,alpha);return 0;
}
