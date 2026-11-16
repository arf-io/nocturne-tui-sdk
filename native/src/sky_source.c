#include "internal.h"
#include "original_math.h"
#include "source_weather.h"
#include "source_compositor.h"
#include "window_palette_source.h"
/* Exact retained WorldStarfield / BlackHoleRenderer.sky. Source +Z becomes native -Z once. */
static int bounded(double x,double a,double b){return x>=a&&x<=b;}
int nrValidSourceSky(const State*s){const SourceSky*a=&s->sourceSky;if(!a->enabled){const uint8_t*p=(const uint8_t*)a;for(size_t i=0;i<sizeof(*a);i++)if(p[i])return 0;return 1;}return s->schema>=NR_STATE_SCHEMA_CAMERA_ANCHOR&&a->enabled==1&&!a->reserved&&a->density>=1&&a->density<=18&&bounded(a->radius,80,360)&&bounded(a->exposure,100,30000)&&bounded(a->trailMs,0,250)&&bounded(a->textLightness,.35,.95)&&bounded(a->textChroma,0,.3);}
static int number(const Json*j,const char*key,double*v,double lo,double hi){int t=nrField(j,0,key);return t<0||(nrNumber(j,t,v)&&bounded(*v,lo,hi));}
int nrSourceSkyCommand(NrContext*c,State*s,const Json*j){(void)c;int profile=nrField(j,0,"starProfile"),changed=profile>=0;const char*names[]={"worldSeed","skyDensity","skyRadius","skyExposure","trailMs","textLightness","textChroma"};for(int k=0;k<7;k++)changed|=nrField(j,0,names[k])>=0;if(!changed)return 0;
 if(profile>=0&&nrEqual(j,profile,"default")){for(int k=0;k<7;k++)if(nrField(j,0,names[k])>=0)return -1;memset(&s->sourceSky,0,sizeof(s->sourceSky));return 0;}
 if(profile>=0&&!nrEqual(j,profile,"source"))return -1;SourceSky*a=&s->sourceSky;if(!a->enabled)*a=(SourceSky){1,2030,9,0,280,6500,65,.83,.1};
 double seed=a->seed,density=a->density;if(!number(j,"worldSeed",&seed,0,4294967295.0)||seed!=nrFloor(seed)||!number(j,"skyDensity",&density,1,18)||density!=nrFloor(density)||!number(j,"skyRadius",&a->radius,80,360)||!number(j,"skyExposure",&a->exposure,100,30000)||!number(j,"trailMs",&a->trailMs,0,250)||!number(j,"textLightness",&a->textLightness,.35,.95)||!number(j,"textChroma",&a->textChroma,0,.3))return -1;a->seed=(uint32_t)seed;a->density=(uint32_t)density;return nrValidSourceSky(s)?0:-1;
}
typedef struct {Camera camera;Vec3 right,up,forward;double focal;uint32_t width,height;} SkyProjection;
static SkyProjection projection(Camera c,uint32_t width,uint32_t height){
 double y=c.yaw*NR_PI/180,p=c.pitch*NR_PI/180,r=c.roll*NR_PI/180,cy=nrOriginalCos(y),sy=nrOriginalSin(y),cp=nrOriginalCos(p),sp=nrOriginalSin(p),cr=nrOriginalCos(r),sr=nrOriginalSin(r);Vec3 right=nrV(cy,0,sy),up=nrV(-sy*sp,cp,cy*sp);
 return (SkyProjection){c,nrAdd(nrScale(right,cr),nrScale(up,sr)),nrSub(nrScale(up,cr),nrScale(right,sr)),nrV(sy*cp,sp,-cy*cp),width/(2*nrOriginalTan(c.fov*NR_PI/360)),width,height};
}
static int project(const SkyProjection*p,Vec3 point,double*out){Vec3 d=nrSub(point,p->camera.position);double depth=nrDot(d,p->forward);if(depth<p->camera.nearPlane||depth>p->camera.farPlane)return 0;out[0]=p->width/2.0+nrDot(d,p->right)*p->focal/depth;out[1]=p->height/2.0-nrDot(d,p->up)*(p->focal/2)/depth;return 1;}
static double unit(uint32_t seed,uint32_t index){return nrHash(seed^((index+1)*0x9e3779b1u))/4294967296.0;}
static double distanceInk(double d,double lum,const SourceSky*a){if(d>=a->radius)return 0;double u=nrClamp((a->radius-d)/(a->radius*.28),0,1);return(1-nrOriginalExp(-lum*a->exposure/(16+d*d)))*(u*u*(3-2*u));}
void nrDrawSourceSky(NrContext*c){const State*s=nrView(c);const SourceSky*a=&s->sourceSky;if(!a->enabled)return;
 if(!s->windowApplication.enabled)for(uint32_t y=0;y<s->height;y++)for(uint32_t x=0;x<s->width;x++){uint32_t pixels[8];int32_t depths[8];for(int k=0;k<8;k++){size_t i=(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2;pixels[k]=c->backgroundPixels[i];depths[k]=c->sourceDepth[i];}NrCell*out=&c->cells[(size_t)y*s->width+x];if(c->sourceActive&&x<(uint32_t)c->sourceWidth&&y<(uint32_t)c->sourceHeight)nrResolveSourceSamples(out,pixels,depths,c->sourceBackground,c->sourceSampling);else nrResolveSamples(out,pixels,pixels,0,s->sampling);}
 Camera current=nrCameraAt(s);uint64_t exposure=(uint64_t)(a->trailMs*1000+.5);Camera previous=nrCameraAtTime(s,s->timeUs>exposure?s->timeUs-exposure:0);SkyProjection p=projection(current,s->width,s->height),old=projection(previous,s->width,s->height);double cx=current.position.x,cy=current.position.y,cz=-current.position.z,r=a->radius;uint32_t wheel[360];for(int h=0;h<360;h++)nrWindowPaletteSourceTextInk(a->textLightness,a->textChroma,h,&wheel[h]);
 for(int z=(int)nrFloor((cz-r)/80);z<=(int)nrFloor((cz+r)/80);z++)for(int y=(int)nrFloor((cy-r)/80);y<=(int)nrFloor((cy+r)/80);y++)for(int x=(int)nrFloor((cx-r)/80);x<=(int)nrFloor((cx+r)/80);x++){
 double dx=nrClamp(x*80-cx,0,1e300),dy=nrClamp(y*80-cy,0,1e300),dz=nrClamp(z*80-cz,0,1e300);if(cx-(x+1)*80>dx)dx=cx-(x+1)*80;if(cy-(y+1)*80>dy)dy=cy-(y+1)*80;if(cz-(z+1)*80>dz)dz=cz-(z+1)*80;if(dx*dx+dy*dy+dz*dz>r*r)continue;
 uint32_t seed=nrHash(a->seed^(uint32_t)x*73856093u^(uint32_t)y*19349663u^(uint32_t)z*83492791u);
 for(uint32_t i=0;i<a->density;i++){Vec3 star=nrV((x+unit(seed,i*5))*80,(y+unit(seed,i*5+1))*80,-(z+unit(seed,i*5+2))*80);double random=unit(seed,i*5+3),lum=.35+((random*random)*(random*random))*24,hue=unit(seed,i*5+4)*360,d=nrOriginalHypot(star.x-cx,star.y-cy,star.z-current.position.z),alpha=distanceInk(d,lum,a),q[2],b[2];if(alpha<.008||!project(&p,star,q)||q[0]<0||q[1]<0||q[0]>=s->width||q[1]>=s->height)continue;uint32_t color=wheel[(int)nrFloor(hue+.5)%360];
 if(a->trailMs>0&&project(&old,star,b)&&nrOriginalHypot(q[0]-b[0],(q[1]-b[1])*2,0)<30)nrSourceWeatherDrawSegment(q[0],q[1],b[0],b[1],color,alpha*.5,s->width,s->height,(uint32_t*)c->cells);
 nrSourcePaintCell(q[0],q[1],d<18?0x22c6:d<55?0x2219:0xb7,color,alpha,s->width,s->height,(uint32_t*)c->cells);
 }}
 static const unsigned bits[8]={1,8,2,16,4,32,64,128};for(uint32_t y=0;y<s->height;y++)for(uint32_t x=0;x<s->width;x++){const NrCell*v=&c->cells[(size_t)y*s->width+x];for(int k=0;k<8;k++){uint32_t g=v->glyph;int fg=g==0x2588||(g==0x2580&&k<4)||(g==0x2584&&k>=4)||(g==0x258c&&!(k%2))||(g==0x2590&&k%2)||(g>=0x2800&&g<=0x28ff&&((g-0x2800)&bits[k]));c->backgroundPixels[(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2]=fg?v->foreground:v->background;}}
}
