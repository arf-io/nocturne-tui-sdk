#include "internal.h"
#include "original_math.h"
#include "observatory_source_background.h"
#include "window_source_math.h"
#include <float.h>

static const char *styles[]={"linear","double-axis","wave","plasma","caustics","vortex","contours","aurora","woven","moire","tunnel","diamond","bilinear","checker","warp"};
static const char *samplings[]={"half","vertical","braille","cell"};
static const char *effects[]={"fade","bounce","genie","roll-up","roll-down","drawer-left","drawer-right","drawer-top","drawer-bottom","center","top-left","top-right","bottom-left","bottom-right","iris","explosion","accordion","portal","orbital-bloom","venetian","ribbon-unfurl"};
static int fail(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static int bounded(double n,double a,double b){return n==n&&n>=a&&n<=b;}
static double fract(double x){return x-nrFloor(x);}
static double seconds(const WindowApplication*a,uint64_t now){return (double)(now/1000-a->atUs/1000)/1000.0;}
static double clockMs(const WindowApplication*a,uint64_t now){return a->motionMs+seconds(a,now)*1000;}
uint64_t nrWindowApplicationTimeUs(const State*s){return s->windowApplication.enabled?(uint64_t)(clockMs(&s->windowApplication,s->timeUs)*1000+.5):s->timeUs;}
static void flightAt(const WindowApplication*a,double ms,double*out){
 unsigned slot=0;for(unsigned i=1;i<a->flightCount;i++){if(a->flight[i][0]>ms)break;slot=i;}
 const double*r=a->flight[slot];for(int k=0;k<3;k++)out[k]=r[k+1]+(ms-r[0])*r[k+4]/1000;
}
static void flightSet(WindowApplication*a){
 double ms=a->motionMs,pos[3];flightAt(a,ms,pos);
 while(a->flightCount&&a->flight[a->flightCount-1][0]>=ms)a->flightCount--;
 if(a->flightCount==256){memmove(a->flight,a->flight+1,255*sizeof(*a->flight));a->flightCount--;}
 double*r=a->flight[a->flightCount++],yaw=a->travelYaw*NR_PI/180,pitch=a->travelPitch*NR_PI/180;
 r[0]=ms;for(int k=0;k<3;k++)r[k+1]=pos[k];
 r[4]=a->starSpeed*nrWindowSourceSin(yaw)*nrWindowSourceCos(pitch);r[5]=a->starSpeed*nrWindowSourceSin(pitch);r[6]=a->starSpeed*nrWindowSourceCos(yaw)*nrWindowSourceCos(pitch);
}
static void defaults(WindowApplication*a){
 memset(a,0,sizeof(*a));a->enabled=1;a->paletteWindowId=1;a->backgroundStyle=1;a->motion=1;
 a->fps=60;a->gradientScreens=.75;a->gradientAngle=-18;a->gradientSpeed=.06;a->pivotX=a->pivotY=.5;a->axisPitch=20;
 a->rotationSpeed=4;a->secondAxisSpeed=2;a->swingAngle=60;a->swingSeconds=16;a->starDensity=.035;
 const uint32_t glyphs[]={46,0xb7,0x2219,0x22c5,0x2801,0x2802,0x2804,0x2840,0x2808,0x2810,0x2820,0x2880};
 memcpy(a->starGlyphs,glyphs,sizeof(glyphs));a->starGlyphCount=12;
 a->starCount=420;a->starSpeed=5;a->trailMs=65;a->flightCount=1;a->flight[0][6]=5;
 a->weatherIntensity=.65;a->novaStrength=.85;a->novaRegularity=3;nrSourceWeatherDefaults(&a->particles);
}
/* Observatory retains the original scalar speed timeline. Direction changes
 * rotate its whole authored travel vector rather than integrating a new bend. */
static double observatoryTravel(const WindowApplication*a,double ms){uint32_t i=a->flightCount-1;while(i&&a->flight[i][0]>ms)i--;return a->flight[i][1]+a->flight[i][4]*(ms-a->flight[i][0])/1000;}
static void observatorySpeed(WindowApplication*a,int fresh){double at=a->motionMs,position=fresh?0:observatoryTravel(a,at);if(fresh){memset(a->flight,0,sizeof(a->flight));a->flightCount=1;a->flight[0][0]=at;}else if(a->flight[a->flightCount-1][0]!=at){if(a->flightCount==256){memmove(a->flight,a->flight+1,255*sizeof(*a->flight));a->flightCount--;}memset(a->flight[a->flightCount],0,sizeof(*a->flight));a->flight[a->flightCount++][0]=at;}double*r=a->flight[a->flightCount-1];r[1]=position;r[4]=a->starSpeed;}
static int applicationParticlesValid(const WindowApplication*a){NrSourceWeatherOptions p=a->particles;if(a->scene==3){if(!bounded(p.lifeMs,200,8000)||!bounded(p.launchSpeed,1,50))return 0;p.launchSpeed=12;}return nrSourceWeatherValidate(&p);}
static int enumField(const Json*j,const char*name,const char*const*names,int n,uint32_t*out){int t=nrField(j,0,name);if(t<0)return 1;for(int k=0;k<n;k++)if(nrEqual(j,t,names[k])){*out=(uint32_t)k;return 1;}return 0;}
static int eventValid(const NrSourceWeatherEvent*e,int atelier){return e->kind<6&&(atelier?(bounded(e->id,-1e12,1e12)&&bounded(e->x,-1e12,1e12)&&bounded(e->y,-1e12,1e12)&&bounded(e->atMs,-1e12,1e12)):(bounded(e->id,0,9007199254740991.0)&&bounded(e->x,-100000,100000)&&bounded(e->y,-100000,100000)&&bounded(e->atMs,0,9007199254740991.0)));}
/* Counts are captured by the active prompt owner before its mutation. The
 * retained source chooses draft emission using UTF16 length, but positions by
 * Unicode scalar count. No prompt storage is duplicated here. */
static uint32_t inputWeatherKind(const WindowApplication*a){return a->reserved?a->reserved-1:a->scene==2?1:5;}
static void inputWeatherEvent(State*s,uint64_t index){
 WindowApplication*a=&s->windowApplication;uint64_t columns=s->width>12?s->width-12:1;
 NrSourceWeatherEvent e={0};e.id=++a->eventSerial;e.kind=inputWeatherKind(a);e.x=5+(double)(index%columns);e.y=(double)s->height-4;e.atMs=clockMs(a,s->timeUs);
 if(a->eventCount==128){memmove(a->events,a->events+1,127*sizeof(*a->events));a->eventCount--;}
 a->events[a->eventCount++]=e;
}
int nrWindowApplicationInput(State*s,uint64_t priorScalarCount,uint64_t insertedScalarCount){
 if(s->schema<NR_STATE_SCHEMA_ATELIER_APP_PARTICLES||!s->windowApplication.enabled)return 0;
 uint64_t columns=s->width>12?s->width-12:1,start=priorScalarCount%columns,count=insertedScalarCount<32?insertedScalarCount:32;
 for(uint64_t i=0;i<count;i++)inputWeatherEvent(s,start+i);return 1;
}
int nrWindowApplicationDraft(State*s,uint64_t priorUtf16Units,uint64_t nextUtf16Units,uint64_t nextScalarCount,int64_t firstDifference){
 if(s->schema<NR_STATE_SCHEMA_ATELIER_APP_PARTICLES||!s->windowApplication.enabled)return 0;
 if(nextUtf16Units>=priorUtf16Units)inputWeatherEvent(s,nextScalarCount);
 else if(firstDifference>=0)inputWeatherEvent(s,(uint64_t)firstDifference);
 return 1;
}
int nrWindowApplicationCommand(NrContext*c,State*s,const Json*j){
 if(s->schema<NR_STATE_SCHEMA_WINDOW_APPLICATION)return fail(c,"Window application requires current schema");
 if(nrEqual(j,nrField(j,0,"op"),"remove-window-application")){if(!nrAllowed(j,0,"op"))return fail(c,"Unknown application field");memset(&s->windowApplication,0,sizeof(s->windowApplication));memset(&s->atelierApplicationParticles,0,sizeof(s->atelierApplicationParticles));return 0;}
 if(nrEqual(j,nrField(j,0,"op"),"window-application-event")){
  WindowApplication*a=&s->windowApplication;if(!a->enabled||!nrAllowed(j,0,"op kind id x y atMs"))return fail(c,"Invalid application event");
  static const char*kinds[]={"embers","sparks","nova","rain","snow","ripples"};
  NrSourceWeatherEvent e={0};e.id=a->eventSerial+1;e.atMs=clockMs(a,s->timeUs);
  if(nrField(j,0,"kind")<0||!enumField(j,"kind",kinds,6,&e.kind))return fail(c,"Invalid event kind");
  const char*names[]={"id","x","y","atMs"};double*values[]={&e.id,&e.x,&e.y,&e.atMs};
  for(int k=0;k<4;k++){int t=nrField(j,0,names[k]);if(t>=0&&!nrNumber(j,t,values[k]))return fail(c,"Invalid event number");}
  if(!eventValid(&e,a->scene==2&&s->schema>=NR_STATE_SCHEMA_ATELIER_APP_PARTICLES))return fail(c,"Invalid event bounds");
  if(a->eventCount==128){memmove(a->events,a->events+1,127*sizeof(*a->events));a->eventCount--;}
  a->events[a->eventCount++]=e;a->eventSerial=e.id;return 0;
 }
 if(!nrAllowed(j,0,"op paletteWindowId scene fps backgroundStyle sampling orbitMode motion gradientScreens gradientAngle gradientSpeed gradientPhase pivotX pivotY axisPitch rotationSpeed secondAxisSpeed swingAngle swingSeconds starDensity starGlyphs starCount starSpeed trailMs travelYaw travelPitch weatherIntensity novaStrength novaRegularity particles atelierParticles weatherStyle weatherLifeMs weatherSpeed"))return fail(c,"Unknown application field");
 WindowApplication a=s->windowApplication;uint32_t priorScene=a.enabled?a.scene:UINT32_MAX;if(!a.enabled){defaults(&a);a.atUs=s->timeUs;if(s->schema>=NR_STATE_SCHEMA_ATELIER_APP_PARTICLES)a.eventSerial=6;}
 else {double dt=seconds(&a,s->timeUs);a.motionMs+=dt*1000;a.travel+=dt*a.gradientSpeed;a.orbit+=dt*a.rotationSpeed;a.orbit2+=dt*a.secondAxisSpeed;a.atUs=s->timeUs;}
 static const char*scenes[]={"windows","shapes","atelier-windows","observatory"},*orbits[]={"spin","pendulum"};
 if(!enumField(j,"scene",scenes,4,&a.scene)||!enumField(j,"backgroundStyle",styles,15,&a.backgroundStyle)||!enumField(j,"sampling",samplings,4,&a.sampling)||!enumField(j,"orbitMode",orbits,2,&a.orbitMode))return fail(c,"Invalid application enum");
 if(a.scene==3&&s->schema<0x20261091u)return fail(c,"Observatory requires schema91");
 if(a.scene==3&&priorScene!=3){a.weatherIntensity=.38;a.novaStrength=.28;a.particles.lifeMs=2400;a.particles.launchSpeed=12;}
 if(a.scene!=3&&(nrField(j,0,"weatherLifeMs")>=0||nrField(j,0,"weatherSpeed")>=0))return fail(c,"Observatory weather aliases require Observatory scene");

 int wt=nrField(j,0,"weatherStyle");if(wt>=0){static const char*names[]={"embers","sparks","nova","rain","snow","ripples"};uint32_t kind=0;if(s->schema<NR_STATE_SCHEMA_ATELIER_APP_PARTICLES||!enumField(j,"weatherStyle",names,6,&kind))return fail(c,"Invalid application weather style");a.reserved=kind+1;}
 struct F{const char*name;double*value;double lo,hi;}fields[]={
 {"starCount",&a.starCount,0,1200},{"starSpeed",&a.starSpeed,0,40},{"trailMs",&a.trailMs,0,250},{"travelYaw",&a.travelYaw,-180,180},{"travelPitch",&a.travelPitch,-89,89},{"weatherIntensity",&a.weatherIntensity,0,1},{"novaStrength",&a.novaStrength,0,1},{"novaRegularity",&a.novaRegularity,0,60},{"fps",&a.fps,1,120},{"gradientScreens",&a.gradientScreens,.05,8},{"gradientAngle",&a.gradientAngle,-360,360},{"gradientSpeed",&a.gradientSpeed,-2,2},{"gradientPhase",&a.gradientPhase,-8,8},{"pivotX",&a.pivotX,-3,4},{"pivotY",&a.pivotY,-3,4},{"axisPitch",&a.axisPitch,-180,180},{"rotationSpeed",&a.rotationSpeed,-90,90},{"secondAxisSpeed",&a.secondAxisSpeed,-90,90},{"swingAngle",&a.swingAngle,0,180},{"swingSeconds",&a.swingSeconds,.5,90},{"starDensity",&a.starDensity,0,.3}};
 for(size_t k=0;k<sizeof(fields)/sizeof(fields[0]);k++){int t=nrField(j,0,fields[k].name);if(t>=0&&(!nrNumber(j,t,fields[k].value)||!bounded(*fields[k].value,fields[k].lo,fields[k].hi)))return fail(c,"Invalid application number");}
 int token=nrField(j,0,"paletteWindowId");if(token>=0){double id;if(!nrNumber(j,token,&id)||!bounded(id,1,65535)||id!=(uint32_t)id)return fail(c,"Invalid palette window");a.paletteWindowId=(uint32_t)id;}
 token=nrField(j,0,"motion");if(token>=0){int motion;if(!nrBoolean(j,token,&motion))return fail(c,"Invalid application motion");a.motion=(uint32_t)motion;}
 token=nrField(j,0,"starGlyphs");if(token>=0){memset(a.starGlyphs,0,sizeof(a.starGlyphs));int count=nrDecode(j,token,a.starGlyphs,64);if(count<1)return fail(c,"Invalid star glyphs");a.starGlyphCount=(uint32_t)count;}
 int pt=nrField(j,0,"particles");if(pt>=0){
  if(a.scene==3&&!nrAllowed(j,pt,"lifeMs launchSpeed"))return fail(c,"Observatory particles accept only lifeMs and launchSpeed");
  if(!nrAllowed(j,pt,"count lifeMs launchSpeed gravity drag wind flickerHz trailMs branches arcSegments arcJitter coreMs shockwave explosionForce seed brightness emberSpread arcReach glyphs"))return fail(c,"Invalid particle field");
  const char*names[]={"count","lifeMs","launchSpeed","gravity","drag","wind","flickerHz","trailMs","branches","arcSegments","arcJitter","coreMs","shockwave","explosionForce","seed","brightness","emberSpread","arcReach"};
  double*values[]={&a.particles.count,&a.particles.lifeMs,&a.particles.launchSpeed,&a.particles.gravity,&a.particles.drag,&a.particles.wind,&a.particles.flickerHz,&a.particles.trailMs,&a.particles.branches,&a.particles.arcSegments,&a.particles.arcJitter,&a.particles.coreMs,&a.particles.shockwave,&a.particles.explosionForce,&a.particles.seed,&a.particles.brightness,&a.particles.emberSpread,&a.particles.arcReach};
  for(int k=0;k<18;k++){int t=nrField(j,pt,names[k]);if(t>=0&&!nrNumber(j,t,values[k]))return fail(c,"Invalid particle number");}
  int t=nrField(j,pt,"glyphs");if(t>=0){memset(a.particles.glyphs,0,sizeof(a.particles.glyphs));int n=nrDecode(j,t,a.particles.glyphs,64);if(n<1)return fail(c,"Invalid particle glyphs");a.particles.glyphCount=(uint32_t)n;}
  if(a.scene!=3&&!nrSourceWeatherValidate(&a.particles))return fail(c,"Invalid particle bounds");
 }
 if(a.scene==3){
  const char*aliases[]={"weatherLifeMs","weatherSpeed"},*nested[]={"lifeMs","launchSpeed"};double*values[]={&a.particles.lifeMs,&a.particles.launchSpeed};const double lo[]={200,1},hi[]={8000,50};
  for(int k=0;k<2;k++){int t=nrField(j,0,aliases[k]);if(t>=0){double value;if(!nrNumber(j,t,&value)||!bounded(value,lo[k],hi[k]))return fail(c,"Invalid Observatory weather control");int n=pt>=0?nrField(j,pt,nested[k]):-1;if(n>=0&&value!=*values[k])return fail(c,"Conflicting Observatory weather controls");*values[k]=value;}}
 }
 if(!applicationParticlesValid(&a))return fail(c,"Invalid application particle bounds");
 int slot=nrFindWindow(s,a.paletteWindowId);if(slot<0||!s->windowContent[slot].enabled)return fail(c,"Palette window needs generated content");
 if(a.scene==3){if(priorScene!=3||nrField(j,0,"starSpeed")>=0)observatorySpeed(&a,priorScene!=3);}else if(nrField(j,0,"starSpeed")>=0||nrField(j,0,"travelYaw")>=0||nrField(j,0,"travelPitch")>=0)flightSet(&a);
 int atelier=nrField(j,0,"atelierParticles");if(atelier>=0||(a.scene==2&&s->schema>=NR_STATE_SCHEMA_ATELIER_APP_PARTICLES)){if(s->schema<NR_STATE_SCHEMA_ATELIER_APP_PARTICLES||nrAtelierApplicationParticlePatch(c,s,j,atelier)<0)return fail(c,"Invalid Atelier application particle controls");}
 s->windowApplication=a;return 0;
}
int nrValidWindowApplication(const State*s){
 const WindowApplication*a=&s->windowApplication;
 if(!a->enabled){WindowApplication empty={0};return !memcmp(a,&empty,sizeof(empty));}
 if(s->schema<NR_STATE_SCHEMA_WINDOW_APPLICATION||a->enabled!=1||a->scene>3||(a->scene==3&&s->schema<0x20261091u)||(a->scene==2&&s->schema<NR_STATE_SCHEMA_ATELIER_WINDOWS)||a->backgroundStyle>14||a->sampling>3||a->orbitMode>1||a->motion>1||a->atUs>s->timeUs||!a->starGlyphCount||a->starGlyphCount>64)return 0;
 int slot=nrFindWindow(s,a->paletteWindowId);if(slot<0||!s->windowContent[slot].enabled)return 0;
 if(!bounded(a->fps,1,120)||!bounded(a->gradientScreens,.05,8)||!bounded(a->gradientAngle,-360,360)||!bounded(a->gradientSpeed,-2,2)||!bounded(a->gradientPhase,-8,8)||!bounded(a->pivotX,-3,4)||!bounded(a->pivotY,-3,4)||!bounded(a->axisPitch,-180,180)||!bounded(a->rotationSpeed,-90,90)||!bounded(a->secondAxisSpeed,-90,90)||!bounded(a->swingAngle,0,180)||!bounded(a->swingSeconds,.5,90)||!bounded(a->starDensity,0,.3)||!bounded(a->motionMs,0,86400000)||!bounded(a->travel,-172800,172800)||!bounded(a->orbit,-7776000,7776000)||!bounded(a->orbit2,-7776000,7776000))return 0;
 if(!bounded(a->starCount,0,1200)||!bounded(a->starSpeed,0,40)||!bounded(a->trailMs,0,250)||!bounded(a->travelYaw,-180,180)||!bounded(a->travelPitch,-89,89)||a->flightCount<1||a->flightCount>256||a->flightReserved)return 0;
 for(uint32_t i=0;i<a->flightCount;i++){const double*r=a->flight[i];if(!bounded(r[0],0,a->motionMs)||(i&&r[0]<=a->flight[i-1][0]))return 0;for(int k=1;k<7;k++)if(!bounded(r[k],-1e16,1e16))return 0;}
 if(!applicationParticlesValid(a)||a->eventCount>128||(s->schema>=NR_STATE_SCHEMA_ATELIER_APP_PARTICLES?a->reserved>6:a->reserved!=0)||!bounded(a->weatherIntensity,0,1)||!bounded(a->novaStrength,0,1)||!bounded(a->novaRegularity,0,60)||!bounded(a->eventSerial,a->scene==2&&s->schema>=NR_STATE_SCHEMA_ATELIER_APP_PARTICLES?-1e12:0,9007199254740991.0))return 0;
 for(uint32_t k=0;k<a->eventCount;k++)if(!eventValid(&a->events[k],a->scene==2&&s->schema>=NR_STATE_SCHEMA_ATELIER_APP_PARTICLES))return 0;
 for(uint32_t k=0;k<64;k++){uint32_t g=a->starGlyphs[k];if(k<a->starGlyphCount){if(g<32||g>0x10ffff||(g>=0xd800&&g<=0xdfff))return 0;}else if(g)return 0;}
 return 1;
}
static double atanSmall(double x){double y=x/(1+nrSqrt(1+x*x)),q=y*y,t=y,sum=y;for(int k=3;k<=81;k+=2){t*=-q;sum+=t/k;}return 2*sum;}
static double angle(double y,double x){if(!x&&!y)return 0;double ax=nrAbs(x),ay=nrAbs(y),a=ax>=ay?atanSmall(ay/ax):NR_PI/2-atanSmall(ax/ay);if(x<0)a=NR_PI-a;return y<0?-a:a;}
static double logarithm(double x){int e=0;while(x<.75){x*=2;e--;}while(x>1.5){x*=.5;e++;}double y=(x-1)/(x+1),q=y*y,t=y,sum=y;for(int k=3;k<65;k+=2){t*=q;sum+=t/k;}return 2*sum+e*.693147180559945309417;}
static double field(const WindowApplication*o,uint64_t now,double nx,double ny){
 double dt=seconds(o,now),t=clockMs(o,now)/1000;double(*sourceSin)(double)=o->scene==3?nrOriginalSin:nrWindowSourceSin;double(*sourceCos)(double)=o->scene==3?nrOriginalCos:nrWindowSourceCos;
 double a=(o->gradientAngle+o->orbit+dt*o->rotationSpeed)*NR_PI/180,b=(o->axisPitch+o->orbit2+dt*o->secondAxisSpeed)*NR_PI/180;
 if(o->orbitMode){a=(o->gradientAngle+sourceSin(t*2*NR_PI/o->swingSeconds)*o->swingAngle)*NR_PI/180;b=(o->axisPitch+sourceSin(t*2*NR_PI/o->swingSeconds+.7)*o->swingAngle*.5)*NR_PI/180;}
 double x=nx-o->pivotX,y=ny-o->pivotY,xr=x*sourceCos(a)-y*sourceSin(a),yr=x*sourceSin(a)+y*sourceCos(a),z=yr*sourceSin(b),v=yr*sourceCos(b),r=nrSqrt(xr*xr+v*v),ang=angle(v,xr),p=xr;
 switch(o->backgroundStyle){
 case 0:p=nx*sourceCos(o->gradientAngle*NR_PI/180)+ny*sourceSin(o->gradientAngle*NR_PI/180);break;
 case 1:p=xr+z*.6;break;
 case 2:p=xr+sourceSin(v*8+t*.5)*.16;break;
 case 3:p=(sourceSin(xr*6+t*.4)+sourceSin(v*8-t*.6)+sourceSin((xr+v)*5+t*.3)+sourceSin(r*9-t*.4))*.18;break;
 case 4:p=nrAbs(sourceSin(xr*8+t*.23)+sourceSin(v*10-t*.36))*.22+sourceSin((xr+v)*12+t*.5)*.1;break;
 case 5:p=r*.6+sourceSin(ang*3+r*14-t*.9)*.22;break;
 case 6:p=sourceSin(xr*3+t*.17)*.3+sourceSin(v*4-t*.21)*.3;break;
 case 7:p=v+.2*sourceSin(xr*6+t*.3)+.08*sourceSin(xr*17-t*.6);break;
 case 8:p=sourceSin(xr*18+t*.4)*sourceCos(v*15-t*.3)*.3;break;
 case 9:p=(sourceSin(xr*25+t*.2)+sourceSin((xr*sourceCos(b)-v*sourceSin(b))*26-t*.15))*.17;break;
 case 10:p=-logarithm(r>.025?r:.025)*.3+ang*.06;break;
 case 11:p=nrAbs(xr)+nrAbs(v);break;
 case 12:p=xr*v*2+xr*.4+v*.6;break;
 case 13:p=sourceSin(xr*12)*sourceSin(v*12);break;
 case 14:p=r*.5+sourceSin(ang*3+t*.12)*.07;break;
 }
 return (p+o->travel+dt*o->gradientSpeed+o->gradientPhase)/o->gradientScreens;
}
static uint32_t sourceHash(uint32_t x){x^=x>>16;x*=0x7feb352d;x^=x>>15;x*=0x846ca68b;x^=x>>16;return x;}
static uint32_t mix(uint32_t a,uint32_t b,double t){uint32_t out=0;for(int shift=0;shift<24;shift+=8){double x=(a>>shift)&255,y=(b>>shift)&255;out|=(uint32_t)nrFloor(x*(1-t)+y*t+.5)<<shift;}return out;}
static uint32_t flattened(const NrCell*c){uint32_t g=c->glyph;return g==0x2580||g==0x2584||g==0x258c||g==0x2590?mix(c->foreground,c->background,.5):c->background;}
static int prepare(NrContext*c){const State*s=nrView(c);int slot=nrFindWindow(s,s->windowApplication.paletteWindowId);if(slot<0)return -1;const NrWindowPaletteSourceConfig*p=&s->windowContent[slot].palette;if(!c->windowPaletteValid[slot]||memcmp(p,&c->windowPaletteConfig[slot],sizeof(*p))){if(nrWindowPaletteSourcePrepare(p,&c->windowPalette[slot]))return -1;c->windowPaletteConfig[slot]=*p;c->windowPaletteValid[slot]=1;}return slot;}
static double randomAt(uint32_t seed,uint32_t index){return sourceHash(seed^((index+1)*0x9e3779b9u))/4294967296.0;}
static double wrap(double value){return fract(value/100+.5)*100-50;}
static void warpSky(NrContext*c,const WindowApplication*a,const NrWindowPaletteSourcePrepared*palette){
 const State*s=nrView(c);Camera camera=nrCameraAt(s);double ms=clockMs(a,s->timeUs),travel[3],previous[3];
 flightAt(a,ms,travel);flightAt(a,ms>a->trailMs?ms-a->trailMs:0,previous);
 double cameraPos[3]={camera.position.x,camera.position.y,-camera.position.z};
 for(uint32_t i=0;i<a->starCount;i++){
  double world[3];for(int k=0;k<3;k++)world[k]=cameraPos[k]+wrap((randomAt(7331,i*3+k)-.5)*100-travel[k]-cameraPos[k]);
  double x,y,z;if(!nrWindowSourceProject(s,&camera,nrV(world[0],world[1],-world[2]),&x,&y,&z)||x<0||x>=s->width||y<0||y>=s->height)continue;
  uint32_t color;nrWindowPaletteSourceInk(palette,170+randomAt(2941,i)*160,&color);double alpha=nrClamp(1-z/70,.18,1),xx,yy,zz;
  if(a->trailMs>0&&nrWindowSourceProject(s,&camera,nrV(world[0]+travel[0]-previous[0],world[1]+travel[1]-previous[1],-(world[2]+travel[2]-previous[2])),&xx,&yy,&zz))nrSourceWeatherDrawSegment(x,y,xx,yy,color,alpha,s->width,s->height,(uint32_t*)c->cells);
  NrCell*cell=&c->cells[(size_t)nrFloor(y)*s->width+(size_t)nrFloor(x)];uint32_t bg=flattened(cell);cell->glyph=z<8?'*':z<20?0x2219:0xb7;cell->foreground=mix(bg,color,alpha);cell->background=bg;cell->id=0;
 }
}
void nrWindowApplicationBackground(NrContext*c){
 const State*s=nrView(c);const WindowApplication*a=&s->windowApplication;if(!a->enabled)return;
 int slot=prepare(c);if(slot<0)return;const NrWindowPaletteSourcePrepared*p=&c->windowPalette[slot];const NrWindowPaletteSourceConfig*cfg=&s->windowContent[slot].palette;
 const unsigned bits[]={1,8,2,16,4,32,64,128};double ms=clockMs(a,s->timeUs);
 int warp=a->backgroundStyle==14||(a->scene==3&&s->observatoryOverlay.enabled&&s->observatoryOverlay.kind==4);
 for(uint32_t y=0;y<s->height;y++)for(uint32_t x=0;x<s->width;x++){
  NrCell*v=&c->cells[(size_t)y*s->width+x];v->id=0;v->glyph=32;v->foreground=cfg->inkRgb;v->background=cfg->backgroundRgb;
  if(a->sampling<2){double x1=x+(a->sampling?.25:.5),x2=x+(a->sampling?.75:.5),y1=y+(a->sampling?.5:.25),y2=y+(a->sampling?.5:.75);v->glyph=a->sampling?0x258c:0x2580;nrWindowPaletteSourceColorAt(p,field(a,s->timeUs,x1/s->width,y1/s->height),&v->foreground);nrWindowPaletteSourceColorAt(p,field(a,s->timeUs,x2/s->width,y2/s->height),&v->background);}
  else if(a->sampling==2){unsigned mask=0;for(int k=0;k<8;k++){double f=field(a,s->timeUs,(x+(k%2+.5)/2)/s->width,(y+(k/2+.5)/4)/s->height);if(fract(f)>(sourceHash(x*33+y*977+k*71)%997)/997.0)mask|=bits[k];}v->glyph=0x2800+mask;nrWindowPaletteSourceColorAt(p,field(a,s->timeUs,(x+.5)/s->width,(y+.5)/s->height),&v->foreground);}
  else nrWindowPaletteSourceColorAt(p,field(a,s->timeUs,(x+.5)/s->width,(y+.5)/s->height),&v->background);
  uint32_t n=sourceHash(41041u^x*1973u^y*9277u);if(a->scene!=2&&!warp&&n/4294967296.0<=a->starDensity){uint32_t period=2600+n%5800;double phase=fract((ms+n%period)/period),sin=a->scene==3?nrOriginalSin(phase*NR_PI):nrWindowSourceSin(phase*NR_PI);if(sin<0)sin=0;double alpha=sin*sin;alpha*=alpha;alpha*=alpha;alpha*=a->scene==3?.65:.7;{uint32_t ink;nrWindowPaletteSourceInk(p,n%360,&ink);uint32_t bg=flattened(v);v->foreground=mix(bg,ink,alpha);v->background=bg;v->glyph=a->starGlyphs[n%a->starGlyphCount];}}
 }
 if(a->scene==2){nrAtelierApplicationStars(c,p);nrAtelierApplicationParticles(c);}
 else if(warp){if(a->scene==3)nrObservatorySourceWarp(c,a,p,ms,observatoryTravel(a,ms));else warpSky(c,a,p);}
 if(a->scene==3){nrObservatorySourceWeather(c,a,p,ms);nrDrawOriginalObservatoryOverlay(c,a,p,ms);}
 else if(a->scene!=2)nrSourceWeatherPaintLayer(a->events,a->eventCount,ms,&a->particles,a->weatherIntensity,a->novaStrength,a->novaRegularity,p->wheel,s->width,s->height,(uint32_t*)c->cells);
 for(uint32_t y=0;y<s->height;y++)for(uint32_t x=0;x<s->width;x++){
  const NrCell*v=&c->cells[(size_t)y*s->width+x];for(int k=0;k<8;k++){uint32_t g=v->glyph;int fg=g==0x2588||(g==0x2580&&k<4)||(g==0x2584&&k>=4)||(g==0x258c&&!(k%2))||(g==0x2590&&k%2)||(g>=0x2800&&g<=0x28ff&&((g-0x2800)&bits[k]));c->backgroundPixels[(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2]=fg?v->foreground:v->background;}
 }
}

/* Current Stage components preserve original integer painting and shared hits. */
static void node(NrContext*c,int kind,int x,int y,int width,int height,int style,uint32_t fg,int opacity,uint32_t bg,int bgAlpha,const uint32_t*text,int count,uint32_t hit,uint32_t owner){
 if(width<1||height<1)return;int32_t n[32]={0};n[0]=kind;n[2]=x;n[3]=y;n[4]=width;n[5]=height;n[12]=(int32_t)fg;n[13]=(int32_t)bg;n[14]=opacity;n[15]=bgAlpha;n[16]=style;n[18]=count;n[21]=17;n[22]=24;n[26]=620;n[27]=830;n[30]=1;nrSourceStageDrawTransient(c,n,text,(uint32_t)count,owner,hit);
}
static int append(uint32_t*out,int n,const char*text){for(;*text&&n<2048;text++)out[n++]=(unsigned char)*text;return n;}
static int appendScalars(uint32_t*out,int n,const uint32_t*t,int count){for(int k=0;k<count&&n<2048;k++)out[n++]=t[k];return n;}
static int fixed(uint32_t*out,int n,double value,int digits){if(value<0){n=append(out,n,"-");value=-value;}int64_t v=(int64_t)nrFloor(value*(digits?10:1)+.5);uint32_t text[32];int k=0;do{text[k++]='0'+v%10;v/=10;}while(v);if(digits&&k==1)text[k++]='0';for(int i=k-1;i>=0;i--){out[n++]=text[i];if(digits&&i==1)out[n++]='.';}return n;}
static void label(NrContext*c,int x,int y,int width,const uint32_t*text,int count,uint32_t color,uint32_t hit,uint32_t owner){node(c,0,x,y,width,1,0,color,1000,0,0,text,count,hit,owner);}
void nrWindowApplicationChrome(NrContext*c){
 if(nrView(c)->windowApplication.enabled&&nrView(c)->windowApplication.scene==3)return;
 if(nrView(c)->windowApplication.enabled&&nrView(c)->windowApplication.scene==2){nrAtelierApplicationChrome(c);return;}
 const State*s=nrView(c);const WindowApplication*a=&s->windowApplication;if(!a->enabled)return;int palette=prepare(c),selected=nrFindWindow(s,s->selectedWindow);if(palette<0||selected<0)return;
 const NrWindowPaletteSourcePrepared*p=&c->windowPalette[palette];uint32_t accent,muted,lilac;nrWindowPaletteSourceInk(p,180,&accent);nrWindowPaletteSourceInk(p,250,&muted);nrWindowPaletteSourceInk(p,305,&lilac);uint32_t ink=s->windowContent[palette].palette.inkRgb;
 int width=(int)s->width,height=(int)s->height;uint32_t text[2048];int n=append(text,0,"NOCTURNE / KINETIC ");text[n++]=0xb7;n=append(text,n," ");n=fixed(text,n,a->fps,0);n=append(text,n," FPS ");text[n++]=0xb7;n=append(text,n," OKLCh");label(c,2,1,width-4,text,n,ink,0,0);
 node(c,2,2,3,width-4,1,2,lilac,600,0,0,0,0,0,0);
 const Window*w=&s->windows[selected];const WindowContent*q=&s->windowContent[selected];const char*chrome[]={"mac","windows","gnome","custom"};
 n=append(text,0,"WINDOW THEATRE / ");n=appendScalars(text,n,w->title,w->titleCount);n=append(text,n," / ");int effect=nrEffectAlgorithm(w->effect);n=append(text,n,effect>=0&&effect<21?effects[effect]:"fade");n=append(text,n," / ");n=append(text,n,chrome[s->windowPresentation[selected].options.chrome]);label(c,3,5,width-6,text,n,accent,0,0);
 nrWindowPresentationDrawTheatreToolbar(c,width,&s->windowPresentation[selected].options,1,(uint32_t)w->id);
 n=append(text,0,"SELECTED ");n=appendScalars(text,n,q->label,q->labelCount);n=append(text,n,"  X ");n=fixed(text,n,w->position.x,1);n=append(text,n," Y ");n=fixed(text,n,w->position.y,1);n=append(text,n," Z ");n=fixed(text,n,-w->position.z,1);n=append(text,n,"  ");text[n++]=0xb7;n=append(text,n,"  drag body: move ");text[n++]=0xb7;n=append(text,n," Alt-drag: rotate ");text[n++]=0xb7;n=append(text,n," Shift-wheel: depth");label(c,3,height-11,width-6,text,n,muted,0,0);
 int slots[NR_MAX_WINDOWS],count=0;for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windows[i].used&&s->windowContent[i].enabled)slots[count++]=i;
 for(int i=1;i<count;i++){int key=slots[i],j=i;while(j&&s->windowContent[slots[j-1]].sourceIndex>s->windowContent[key].sourceIndex){slots[j]=slots[j-1];j--;}slots[j]=key;}
 int tab=count?(width-6)/count-1:8;if(tab<8)tab=8;if(tab>28)tab=28;
 for(int i=0;i<count;i++){int k=slots[i];const Window*win=&s->windows[k];const WindowContent*content=&s->windowContent[k];char id[65];for(uint32_t j=0;j<content->labelCount;j++)id[j]=(char)content->label[j];id[content->labelCount]=0;
  const char*name=!strcmp(id,"pearl")?"Signal":!strcmp(id,"atlas")?"Flight":!strcmp(id,"iris")?"Materials":0;n=0;if(name)n=append(text,n,name);else{int start=0;for(int j=0;j+2<win->titleCount;j++)if(win->title[j]==' '&&win->title[j+1]=='/'&&win->title[j+2]==' ')start=j+3;n=appendScalars(text,n,win->title+start,win->titleCount-start);}int max=tab-12;if(max<1)max=1;if(n>max)n=max;n=append(text,n," ");text[n++]=0xb7;n=append(text,n," ");const char*state=!content->visibilityTo?"Restore":content->visibilityTo==.16?"Unfold":win->maximized?"Full":"Open";n=append(text,n,state);uint32_t color=!win->maximized&&content->visibilityTo==1?accent:0xd5b682;node(c,3,3+i*(tab+1),height-9,tab,3,0,color,1000,0x1e2938,880,text,n,NR_ID_DOCK|win->id,(2u<<16)|win->id);
 }
 node(c,2,2,height-5,width-4,1,0,accent,450,0,0,0,0,0,0);
 n=0;text[n++]=0x203a;text[n++]=' ';n=appendScalars(text,n,s->promptDocument.glyphs,s->promptDocument.count);label(c,3,height-4,width-6,text,n,ink,NR_ID_PROMPT,(1u<<16));
 n=append(text,0,a->scene?"SHAPES":"WINDOW THEATRE");label(c,3,height-2,width-6,text,n,muted,0,0);
}
