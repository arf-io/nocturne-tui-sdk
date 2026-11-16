#include "internal.h"
#include "source_weather.h"
#include "window_palette_source.h"
#include "window_source_math.h"
/* Exact RC2 EffectPainter.local ripple layers. Original arrays are scratch;
 * authoritative field data and the existing equation sampler stay untouched. */
static uint32_t mix(uint32_t a,uint32_t b,double p){
 p=nrClamp(p,0,1);uint32_t out=0;for(int k=0;k<=16;k+=8){double aa=(a>>k)&255,bb=(b>>k)&255;out|=(uint32_t)nrFloor(aa*(1-p)+bb*p+.5)<<k;}return out;
}
static uint32_t flat(const uint32_t*c){return c[0]==0x2580||c[0]==0x2584||c[0]==0x258c||c[0]==0x2590?mix(c[1],c[2],.5):c[2];}
static uint32_t ink(const uint32_t*wheel,double hue){int h=(int)nrFloor(hue+.5)%360;if(h<0)h+=360;return wheel[h];}
static void put(uint32_t*tile,int w,int h,double x,double y,uint32_t glyph,uint32_t color,double alpha){
 x=nrFloor(x);y=nrFloor(y);if(x<0||y<0||x>=w||y>=h)return;uint32_t*c=tile+4*((size_t)y*w+(size_t)x),under=flat(c);c[0]=glyph;c[1]=mix(under,color,alpha);c[2]=under;c[3]=0;
}
static double expNegative(double x){if(x>745)return 0;int squares=0;while(x>.125){x*=.5;squares++;}double value=1,term=1;for(int i=1;i<=20;i++){term*= -x/i;value+=term;}while(squares--)value*=value;return value;}
static double randomAt(uint32_t seed,uint32_t i){return nrHash(seed^((i+1u)*2654435769u))/4294967296.0;}
int nrValidOriginalField(const State*s,int i){
 const Field*f=&s->fields[i];const FieldControls*q=&s->fieldControls[i];if(!NR_FIELD_SOURCE_PAINT(q))return 1;
 if(s->schema<NR_STATE_SCHEMA_SURFACE_PAINT||NR_FIELD_OPTICS(q)<1||NR_FIELD_OPTICS(q)>4||q->continuous||q->materialAuthored||q->frequency!=100||q->phase||q->interference||q->falloff!=2)return 0;
 uint32_t profile=NR_FIELD_OPTICS(q);
 if(profile==1&&(f->width<.0625||f->width>32||f->speed<.00390625||f->lifeUs<100000||f->lifeUs>30000000||NR_FIELD_RINGS(q)>6))return 0;
 if(profile==2&&f->width!=1.7)return 0;
 if(profile==3&&(f->speed<1||f->speed>70||f->lifeUs<100000||f->lifeUs>12000000||f->width!=.25))return 0;
 if(profile==4&&(f->width!=1.2||f->speed>70||f->lifeUs<200000||f->lifeUs>10000000))return 0;
 return 1;
}
static void studio(uint32_t*tile,const Field*f,const FieldControls*q,uint64_t age){
 StudioNovaControls b={.seed=f->seed,.novaDurationMs=(uint32_t)(f->lifeUs/1000),.rippleSpeed=(uint32_t)nrFloor(f->speed*256+.5),.rippleWidth=(uint32_t)nrFloor(f->width*256+.5),.rippleOpacity=700,.rippleRings=NR_FIELD_RINGS(q)?NR_FIELD_RINGS(q):3,.cellAspect=2000,.strength=(uint32_t)nrFloor(f->strength*1000+.5),.waveScale=6144,.paletteCount=5,.palette={0x28304f,0x785c89,0x367876,0xae7357,0x504565}};
 for(int y=0;y<44;y++)for(int x=0;x<80;x++){
  int64_t dx=(x-40)*256,dy=(y-22)*256;uint32_t*cell=tile+4*(y*80+x);cell[0]=0x2580;
  for(int half=0;half<2;half++){int64_t yy=dy+(half?64:-64);uint32_t a=nrStudioNovaRing(&b,age,dx,yy),color=nrStudioNovaRingColor(&b,dx,yy),out=0;
   for(int shift=0;shift<=16;shift+=8)out|=(((color>>shift)&255)*a/1000)<<shift;
   cell[half+1]=out;
  }
 }
}
static void observatory(uint32_t*tile,const Field*f,double age,const uint32_t*wheel){
 double radius=age/1000*f->speed,width=f->width,max=radius+width*3,fade=1-age/(f->lifeUs/1000.0),strength=f->strength*fade*fade;
 uint32_t color=ink(wheel,f->seed*53+age*.02);
 int top=(int)nrClamp(nrFloor(22-max/2),0,44),left=(int)nrClamp(nrFloor(40-max),0,80);double bottom=nrClamp(22+max/2,0,44),right=nrClamp(40+max,0,80);
 for(int y=top;y<bottom;y++)for(int x=left;x<right;x++){
  double dx=x-40,dy=(y+.5-22)*2,ring=nrAbs(nrSqrt(dx*dx+dy*dy)-radius),pulse=expNegative(ring*ring/(width*width))*strength*.65;
  uint32_t*c=tile+4*(y*80+x);c[2]=mix(c[2],color,pulse);
 }
}
static void atelier(uint32_t*tile,const Field*f,double age,const uint32_t*wheel){
 double t=age/1000,p=age/(f->lifeUs/1000.0),fade=nrPowPositive(1-p,1.8),radius=t*f->speed;
 /* sampleAtelierBurst receives event.id==options.seed from EffectPainter.local. */
 uint32_t seed=f->seed^f->seed;
 double alpha=fade*.35*f->strength;
 int top=(int)nrClamp(nrFloor(22-radius),0,44),left=(int)nrClamp(nrFloor(40-radius*2),0,80);double bottom=nrClamp(22+radius+1,0,44),right=nrClamp(40+radius*2+1,0,80);
 for(int y=top;y<bottom;y++)for(int x=left;x<right;x++){
  double dx=x-40,dy=(y-22)*2,d=nrSqrt(dx*dx+dy*dy),a=nrClamp(1-nrAbs(d-radius)/f->width,0,1)*alpha;
  if(a>.004){uint32_t*c=tile+4*(y*80+x);c[2]=mix(c[2],ink(wheel,40+.65*30),a);}
 }
 for(uint32_t j=0;j<64;j++){
  double angle=randomAt(seed,j*5)*2*NR_PI,q=randomAt(seed,j*5+2);
  put(tile,80,44,40+nrWindowSourceCos(angle)*t*f->speed*q,22+nrWindowSourceSin(angle)*t*f->speed*q*.5,0xb7,ink(wheel,35+.8*75),nrClamp(fade*.7*f->strength,0,1));
 }
}
void nrDrawOriginalFields(NrContext*c){
 const State*s=nrView(c);uint32_t wheel[360];int ready=0;
 for(int i=0;i<NR_FIELDS;i++){
  const Field*f=&s->fields[i];const FieldControls*q=&s->fieldControls[i];if(!NR_FIELD_SOURCE_PAINT(q)||!nrFieldLive(s,i))continue;
  if(!ready){for(int h=0;h<360;h++)if(nrWindowPaletteSourceTextInk(.83,.1,h,&wheel[h]))return;ready=1;}
  uint32_t tile[80*44*4];memset(tile,0,sizeof(tile));for(int j=0;j<80*44;j++)tile[j*4]=32;
  uint64_t ageUs=s->timeUs-f->atUs;double age=ageUs/1000.0;uint32_t profile=NR_FIELD_OPTICS(q);
  if(profile==1)studio(tile,f,q,ageUs/1000);
  else if(profile==2)observatory(tile,f,age,wheel);
  else if(profile==3){NrSourceWeatherOptions o;nrSourceWeatherDefaults(&o);o.lifeMs=f->lifeUs/1000.0;o.explosionForce=f->speed;o.brightness=f->strength;o.seed=f->seed;NrSourceWeatherEvent event={NR_SOURCE_WEATHER_RIPPLES,f->id,40,22,0};if(nrSourceWeatherPaint(&event,age,&o,1,wheel,80,44,tile))continue;}
  else atelier(tile,f,age,wheel);
  double cx,cy;nrFieldCenter(s,i,&cx,&cy);
  for(int y=0;y<44;y++)for(int x=0;x<80;x++){
   const uint32_t*t=tile+4*(y*80+x);if(!t[2]&&(t[0]==32||!t[1]))continue;
   double xx=nrFloor(cx+x-40+.5),yy=nrFloor(cy+y-22+.5);if(xx<0||yy<0||xx>=s->width||yy>=s->height||!nrFieldContains(s,i,xx,yy))continue;
   uint32_t*d=(uint32_t*)&c->cells[(size_t)yy*s->width+(size_t)xx];double weight=1;
   if(t[2])d[2]=mix(flat(d),t[2],.7*weight);
   if(t[0]!=32&&t[1])put((uint32_t*)c->cells,s->width,s->height,xx,yy,t[0],t[1],.95*weight);
  }
 }
}
