#include "internal.h"
#include "original_math.h"
#include "observatory_source_background.h"
/* Direct port of retained c221beb6 ObservatoryRenderer.warp/weather. The
 * original JS remains an independent test oracle; this paints current cells. */
static double fract(double x){return x-nrFloor(x);}
static uint32_t u32(double x){return (uint32_t)(x-4294967296.0*nrFloor(x/4294967296.0));}
static double randomAt(double seed,uint32_t index){return nrHash(u32(seed)^((index+1u)*0x9e3779b9u))/4294967296.0;}
static uint32_t mix(uint32_t a,uint32_t b,double t){t=nrClamp(t,0,1);uint32_t out=0;for(int shift=0;shift<24;shift+=8){double x=(a>>shift)&255,y=(b>>shift)&255;out|=(uint32_t)nrFloor(x*(1-t)+y*t+.5)<<shift;}return out;}
static uint32_t ink(const NrWindowPaletteSourcePrepared*p,double hue){double h=nrFloor(hue+.5);h-=360*nrFloor(h/360);return p->wheel[(int)h];}
static double hypot2(double x,double y){double v[2]={nrAbs(x),nrAbs(y)},max=v[0]>v[1]?v[0]:v[1];if(!max)return 0;double sum=0,c=0;for(int i=0;i<2;i++){double n=v[i]/max,a=n*n-c,t=sum+a;c=(t-sum)-a;sum=t;}return __builtin_sqrt(sum)*max;}
static void dot(NrContext*c,double px,double py,uint32_t color,double alpha){
 const State*s=nrView(c);static const uint32_t bits[8]={1,8,2,16,4,32,64,128};px=nrFloor(px+.5);py=nrFloor(py+.5);if(px<0||py<0||px>=s->width*2.0||py>=s->height*4.0)return;uint32_t x=(uint32_t)px,y=(uint32_t)py;NrCell*d=&c->cells[(size_t)(y/4)*s->width+x/2];if(d->glyph<0x2800||d->glyph>0x28ff){if(d->glyph==0x2580||d->glyph==0x2584||d->glyph==0x258c||d->glyph==0x2590)d->background=mix(d->foreground,d->background,.5);d->glyph=0x2800;}d->glyph|=bits[(y%4)*2+x%2];d->foreground=mix(d->background,color,alpha);
}
/* Preserve Observatory projectPoint's sequential arithmetic and source +Z.
 * Its pitch convention is distinct from the older window camera basis. */
int nrObservatorySourceProject(const Camera*camera,Vec3 point,double width,double height,double*outX,double*outY,double*outZ){
 double x=point.x-camera->position.x,y=point.y-camera->position.y,z=point.z+camera->position.z;
 double yaw=-camera->yaw*NR_PI/180,pitch=-camera->pitch*NR_PI/180,roll=-camera->roll*NR_PI/180;
 double nextX=x*nrOriginalCos(yaw)+z*nrOriginalSin(yaw),nextZ=-x*nrOriginalSin(yaw)+z*nrOriginalCos(yaw);x=nextX;z=nextZ;
 double nextY=y*nrOriginalCos(pitch)-z*nrOriginalSin(pitch);nextZ=y*nrOriginalSin(pitch)+z*nrOriginalCos(pitch);y=nextY;z=nextZ;
 nextX=x*nrOriginalCos(roll)-y*nrOriginalSin(roll);nextY=x*nrOriginalSin(roll)+y*nrOriginalCos(roll);x=nextX;y=nextY;
 if(!__builtin_isfinite(x+y+z)||z<.2||z>150)return 0;
 double f=width/(2*nrOriginalTan(camera->fov*NR_PI/360));*outX=width/2+x*f/z;*outY=height/2-y*f/z/2;*outZ=z;return 1;
}
void nrObservatorySourceWarp(NrContext*c,const WindowApplication*a,const NrWindowPaletteSourcePrepared*p,double ms,double travel){
 (void)ms;const State*s=nrView(c);Camera authored=nrCameraAt(s),camera=authored;camera.position=nrV(0,0,0);camera.nearPlane=.2;camera.farPlane=150;
 double yaw=a->travelYaw*NR_PI/180,pitch=a->travelPitch*NR_PI/180,velocity[3]={nrOriginalSin(yaw)*nrOriginalCos(pitch),nrOriginalSin(pitch),nrOriginalCos(yaw)*nrOriginalCos(pitch)},position[3]={authored.position.x,authored.position.y,-authored.position.z};
 for(uint32_t i=0;i<(uint32_t)nrFloor(a->starCount);i++){
  double point[3];for(int k=0;k<3;k++)point[k]=fract(((randomAt(7331,i*3+k)-.5)*80-velocity[k]*travel-position[k])/80+.5)*80-40;
  double x,y,z;if(!nrObservatorySourceProject(&camera,nrV(point[0],point[1],point[2]),s->width,s->height,&x,&y,&z)||x<0||y<0||x>=s->width||y>=s->height)continue;
  uint32_t color=ink(p,190+randomAt(2941,i)*130);double alpha=nrClamp(1-z/55,.15,1),exposure=a->starSpeed*a->trailMs/1000,bx,by,bz;
  if(a->trailMs>0&&nrObservatorySourceProject(&camera,nrV(point[0]+velocity[0]*exposure,point[1]+velocity[1]*exposure,point[2]+velocity[2]*exposure),s->width,s->height,&bx,&by,&bz))nrSourceWeatherDrawSegment(x,y,bx,by,color,alpha,s->width,s->height,(uint32_t*)c->cells);
  else dot(c,x*2,y*4,color,alpha);
 }
}
static void event(NrContext*c,const WindowApplication*a,const NrWindowPaletteSourcePrepared*p,const NrSourceWeatherEvent*e,double ms){
 const State*s=nrView(c);double age=ms-e->atMs,life=a->particles.lifeMs,q=age/life,envelope=(1-q)*(1-q),strength=a->weatherIntensity*envelope*(e->kind==NR_SOURCE_WEATHER_NOVA?a->novaStrength:1);uint32_t color=ink(p,e->id*53+age*.02);
 if(e->kind==NR_SOURCE_WEATHER_RIPPLES||e->kind==NR_SOURCE_WEATHER_NOVA){
  double radius=age/1000*a->particles.launchSpeed,width=1.7,max=radius+width*3;int y0=(int)nrFloor(e->y-max/2),x0=(int)nrFloor(e->x-max);if(y0<0)y0=0;if(x0<0)x0=0;double y1=e->y+max/2,x1=e->x+max;if(y1>s->height)y1=s->height;if(x1>s->width)x1=s->width;
  for(int y=y0;y<y1;y++)for(int x=x0;x<x1;x++){NrCell*d=&c->cells[(size_t)y*s->width+x];if(d->glyph==0x2580){double r=nrAbs(hypot2(x-e->x,(y+.25-e->y)*2)-radius),alpha=nrOriginalExp(-r*r/(width*width))*strength*.65;d->foreground=mix(d->foreground,color,alpha);r=nrAbs(hypot2(x-e->x,(y+.75-e->y)*2)-radius);alpha=nrOriginalExp(-r*r/(width*width))*strength*.65;d->background=mix(d->background,color,alpha);}else{double r=nrAbs(hypot2(x-e->x,(y+.5-e->y)*2)-radius),alpha=nrOriginalExp(-r*r/(width*width))*strength*.65;d->background=mix(d->background,color,alpha);}}
  if(e->kind==NR_SOURCE_WEATHER_NOVA&&age<650)nrSourcePaintCell(e->x,e->y,age<200?0x2219:age<430?0x2726:0x2727,color,strength,s->width,s->height,(uint32_t*)c->cells);
 }else{
  uint32_t count=(uint32_t)nrFloor(16+a->weatherIntensity*24+.5);
  for(uint32_t i=0;i<count;i++){double r=randomAt(e->id,i),r2=randomAt(e->id+7919,i),seconds=age/1000,x=e->x,y=e->y;uint32_t glyph=0xb7;
   if(e->kind==NR_SOURCE_WEATHER_RAIN){x+=(r-.5)*20;y-=r2*14;y+=seconds*a->particles.launchSpeed;glyph=i%2?0x2571:0x2502;}
   if(e->kind==NR_SOURCE_WEATHER_SNOW){x+=(r-.5)*24+nrOriginalSin(seconds*2+r2*2*NR_PI)*2;y=y-12-r2*8+seconds*a->particles.launchSpeed*.4;glyph=(const uint32_t[]){0xb7,0x2219,0x22c5}[i%3];}
   if(e->kind==NR_SOURCE_WEATHER_EMBERS){x+=(r-.5)*seconds*8;y-=seconds*a->particles.launchSpeed*(.2+r2*.4);glyph=0x2219;}
   if(e->kind==NR_SOURCE_WEATHER_SPARKS){double angle=r*2*NR_PI;x+=nrOriginalCos(angle)*seconds*a->particles.launchSpeed*r2;y+=nrOriginalSin(angle)*seconds*a->particles.launchSpeed*r2/2+seconds*seconds*2;}
   nrSourcePaintCell(x,y,glyph,color,strength*(.5+r*.5),s->width,s->height,(uint32_t*)c->cells);
  }
 }
}
void nrObservatorySourceWeather(NrContext*c,const WindowApplication*a,const NrWindowPaletteSourcePrepared*p,double ms){
 if(a->weatherIntensity==0)return;uint32_t selected[24],count=0;
 for(uint32_t i=0;i<a->eventCount;i++)if(a->events[i].atMs<=ms&&ms-a->events[i].atMs<a->particles.lifeMs){if(count==24){memmove(selected,selected+1,23*sizeof(*selected));count--;}selected[count++]=i;}
 for(uint32_t i=0;i<count;i++)event(c,a,p,&a->events[selected[i]],ms);
 if(a->novaRegularity>0){const State*s=nrView(c);double period=60000/a->novaRegularity,k=nrFloor(ms/period),first=k>1?k-1:1;for(double i=first;i<=k;i++){double at=i*period;if(ms-at<a->particles.lifeMs){NrSourceWeatherEvent e={.kind=NR_SOURCE_WEATHER_NOVA,.id=i+900000,.x=randomAt(53,(uint32_t)i)*s->width,.y=randomAt(79,(uint32_t)i)*s->height,.atMs=at};event(c,a,p,&e,ms);}}}
}
