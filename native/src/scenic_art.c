/* Source-faithful world-space samplers for the five rc2 scenic compositions.
 * This file owns art geometry only; RC4 owns projection, clipping, depth and
 * cell compositing. Positions and all source arithmetic remain signed Q8. */
#include "scenic_art.h"

#include <limits.h>
#include <stddef.h>

#include "../../src/world_fields.inc"
#include "../../src/world_detail_fields.inc"
#include "../../src/sine.inc"

typedef struct { int32_t x,y,z; } WPoint;
typedef struct {
    const NrScenicArtConfig *config;
    const NrScenicArtSink *sink;
    uint64_t time;
    int hasDetail;
    int32_t sy,cy,sp,cp;
} Art;

static int32_t clampI(int32_t v,int32_t lo,int32_t hi) {
    return v<lo?lo:(v>hi?hi:v);
}
static int32_t modI(int64_t v,int32_t d) {
    int32_t r=(int32_t)(v%d);return r<0?r+d:r;
}
static int32_t sinI(int64_t phase) { return SINE[modI(phase,1024)]; }
static uint32_t hashI(uint32_t v) {
    v^=v>>16;v*=0x7feb352du;v^=v>>15;v*=0x846ca68bu;return v^(v>>16);
}
static int32_t redI(uint32_t c) { return (int32_t)((c>>16)&255); }
static int32_t greenI(uint32_t c) { return (int32_t)((c>>8)&255); }
static int32_t blueI(uint32_t c) { return (int32_t)(c&255); }
static uint32_t rgbI(int32_t r,int32_t g,int32_t b) {
    return ((uint32_t)clampI(r,0,255)<<16)|((uint32_t)clampI(g,0,255)<<8)|(uint32_t)clampI(b,0,255);
}
static int32_t wSin(int64_t angle) {
    int32_t q=modI(angle,360*256);
    int64_t phase=(int64_t)q*1024;
    int32_t k=(int32_t)(phase/(360*256)),r=(int32_t)(phase%(360*256));
    return sinI(k)+(int32_t)((int64_t)(sinI(k+1)-sinI(k))*r/(360*256));
}
static int32_t wCos(int64_t a) { return wSin(a+90*256); }
static int32_t wWave(int64_t phase) { return sinI(phase); }
static uint32_t wMix(uint32_t a,uint32_t b,int32_t t) {
    t=clampI(t,0,1000);
    return rgbI((redI(a)*(1000-t)+redI(b)*t)/1000,
                (greenI(a)*(1000-t)+greenI(b)*t)/1000,
                (blueI(a)*(1000-t)+blueI(b)*t)/1000);
}
static uint32_t wShade(uint32_t a,int32_t t) { return wMix(0,a,t); }
static WPoint wP(int32_t x,int32_t y,int32_t z) { WPoint p={x,y,z};return p; }
static WPoint wV(int32_t x,int32_t y,int32_t z) { return wP(x*256,y*256,z*256); }

static void wTriangle(Art *c,WPoint a,WPoint b,WPoint d,uint32_t color,int32_t alpha) {
    c->sink->triangle(c->sink->user,a.x,a.y,a.z,b.x,b.y,b.z,d.x,d.y,d.z,color,alpha);
}
static void wQuad(Art *c,WPoint a,WPoint b,WPoint d,WPoint e,uint32_t color,int32_t alpha) {
    wTriangle(c,a,b,d,color,alpha);wTriangle(c,a,d,e,color,alpha);
}
static void wDot(Art *c,WPoint p,uint32_t color,int32_t alpha,int32_t radius) {
    c->sink->point(c->sink->user,p.x,p.y,p.z,color,alpha,radius);
}
static void wLine(Art *c,WPoint a,WPoint b,uint32_t color,int32_t alpha) {
    c->sink->line(c->sink->user,a.x,a.y,a.z,b.x,b.y,b.z,color,alpha);
}
static void wBox(Art *c,int32_t x,int32_t y,int32_t z,int32_t sx,int32_t sy,int32_t sz,uint32_t color) {
    WPoint a=wP(x-sx,y,z-sz),b=wP(x+sx,y,z-sz),d=wP(x+sx,y,z+sz),e=wP(x-sx,y,z+sz);
    WPoint u=wP(x-sx,y-sy,z-sz),v=wP(x+sx,y-sy,z-sz),w=wP(x+sx,y-sy,z+sz),t=wP(x-sx,y-sy,z+sz);
    wQuad(c,a,b,d,e,color,1000);wQuad(c,u,v,b,a,wShade(color,600),1000);
    wQuad(c,v,w,d,b,wShade(color,460),1000);wQuad(c,w,t,e,d,wShade(color,730),1000);
    wQuad(c,t,u,a,e,wShade(color,820),1000);
}
static void wTree(Art *c,int32_t x,int32_t y,int32_t z,int32_t h,uint32_t color) {
    wLine(c,wP(x,y,z),wP(x,y+h,z),0x81705e,1000);
    for(int k=0;k<3;k++) {
        int32_t b=y+h*k/4,rad=h*(4-k)/10;WPoint top=wP(x,b+h/2,z);
        WPoint a=wP(x-rad,b,z-rad),d=wP(x+rad,b,z-rad),e=wP(x+rad,b,z+rad),f=wP(x-rad,b,z+rad);
        wTriangle(c,a,d,top,wShade(color,730),1000);wTriangle(c,d,e,top,wShade(color,600),1000);
        wTriangle(c,e,f,top,color,1000);wTriangle(c,f,a,top,wShade(color,900),1000);
    }
}

static WPoint wWaterPoint(int x,int j,int64_t phase) {
    return wP(x*256,(25-j)*256,(-3+x*x/150)*256+wWave((int64_t)x*43+j*23+phase/6)/18);
}
static void wWaterfall(Art *c) {
    const int32_t *v=c->config->world;
    uint32_t rock=v[NR_WORLD_SECONDARY]?(uint32_t)v[NR_WORLD_SECONDARY]:0x35434d;
    uint32_t accent=v[NR_WORLD_ACCENT]?(uint32_t)v[NR_WORLD_ACCENT]:0x86cfc5;
    uint32_t foam=v[NR_WORLD_INK]?(uint32_t)v[NR_WORLD_INK]:0xdde9d7;
    int64_t phase=(int64_t)(c->time%3600000)*v[NR_WORLD_FLOW]/1000;
    for(int z=32;z>=8;z-=8)for(int x=-36;x<=36;x+=6) {
        uint32_t h=hashI((uint32_t)(x*993+z*719)^(uint32_t)v[NR_WORLD_SEED]);
        int32_t y=(21+(int32_t)(h%4))*256;
        wBox(c,x*256,y,z*256,3*256,((int32_t)(h%5)+32)*256,4*256,
             wMix(rock,0x74847a,(int32_t)(h%230)));
    }
    for(int x=-36;x<=36;x+=4) {
        int32_t z=(4+x*x/140)*256;uint32_t h=hashI((uint32_t)(x+55)*717u+(uint32_t)v[NR_WORLD_SEED]);
        wBox(c,x*256,(21+(int32_t)(h%3))*256,z,2*256,(30+(int32_t)(h%6))*256,4*256,
             wMix(rock,0x97a99b,(int32_t)(h%260)));
        for(int k=0;k<5;k++)wLine(c,wP((x-2)*256,(15-k*5)*256,z-4*256-8),
            wP((x+2)*256,(15-k*5)*256,z-4*256-8),wShade(0x92aba7,300+k*25),600);
    }
    for(int a=0;a<64;a++) {
        int an=a*360*256/64,bn=(a+1)*360*256/64;
        WPoint p=wP(wCos(an)*32*256/1000,-11*256,wSin(an)*32*256/1350-20*256);
        WPoint q=wP(wCos(bn)*32*256/1000,-11*256,wSin(bn)*32*256/1350-20*256);
        wQuad(c,p,q,wP(q.x,-18*256,q.z),wP(p.x,-18*256,p.z),wShade(rock,850),1000);
        wQuad(c,p,q,wP(wCos(bn)*29*256/1000,-11*256,wSin(bn)*29*256/1350-20*256),
            wP(wCos(an)*29*256/1000,-11*256,wSin(an)*29*256/1350-20*256),wShade(rock,900),1000);
        if(a%4==0)wBox(c,p.x,-10*256,p.z,256,3*256,256,wMix(rock,0x687f72,350));
    }
    for(int ring=10;ring>=1;ring--)for(int a=0;a<64;a++) {
        int32_t r=ring*3*256;int an=a*360*256/64,bn=(a+1)*360*256/64;
        WPoint center=wV(0,-10,-20);
        WPoint p=wP(wCos(an)*r/1000,-10*256,wSin(an)*r/1350-20*256);
        WPoint q=wP(wCos(bn)*r/1000,-10*256,wSin(bn)*r/1350-20*256);
        wTriangle(c,center,p,q,wMix(0x142b37,accent,110+ring*10),1000);
    }
    for(int z=36;z>=5;z--)for(int x=-11;x<11;x++) {
        int wave=wWave((int64_t)x*37+z*29-phase/7);
        uint32_t co=wMix(0x244454,accent,300+wave/6);
        wQuad(c,wV(x,25,z),wV(x+1,25,z),wV(x+1,25,z+1),wV(x,25,z+1),co,1000);
    }
    if(c->hasDetail&&c->config->detail[NR_WORLD_DETAIL_JOIN_RIVER])for(int x=-12;x<12;x++) {
        WPoint a=wWaterPoint(x,0,phase),b=wWaterPoint(x+1,0,phase);
        wQuad(c,wV(x,25,5),wV(x+1,25,5),b,a,
              wMix(0x244454,accent,380+wWave((int64_t)x*37-phase/7)/6),1000);
    }
    if(v[NR_WORLD_FLOW]>0)for(int x=-12;x<12;x++)for(int j=0;j<36;j++) {
        WPoint a=wWaterPoint(x,j,phase),b=wWaterPoint(x+1,j,phase),d=wWaterPoint(x+1,j+1,phase),e=wWaterPoint(x,j+1,phase);
        int streak=(wWave((int64_t)x*77+j*41+phase/4)+1000)/2;
        wQuad(c,a,b,d,e,wMix(accent,foam,streak*3/5),v[NR_WORLD_WATER_ALPHA]);
    }
    for(int n=0;n<25;n++) {
        int32_t r=(int32_t)((phase*3+(int64_t)n*339)%5000)+700;
        for(int a=0;a<48;a++) {
            int an=a*360*256/48;WPoint p=wP(wCos(an)*r/1000,-10*256+20,-6*256+wSin(an)*r/1800);
            wDot(c,p,wMix(accent,foam,400),clampI(600-r/12,30,500),0);
        }
    }
    for(int n=0;n<160&&v[NR_WORLD_FLOW]>0;n++) {
        uint32_t h=hashI((uint32_t)n*9941u+(uint32_t)v[NR_WORLD_SEED]);
        int age=(int)((phase+(h%3500))%3500);
        WPoint p=wP((int32_t)(h%6000)-3000+wWave((int64_t)n*47+age/8)/4,
                    -9*256+age/2,-3*256-age/6+(int32_t)(h%1100));
        wDot(c,p,foam,clampI((3500-age)/9,0,350),0);
    }
    for(int i=0;i<18;i++) {
        uint32_t h=hashI((uint32_t)i*1811u+(uint32_t)v[NR_WORLD_SEED]);
        int x=(i%2?-1:1)*(18+(int)(h%17)),z=12+(int)(h%21);
        wTree(c,x*256,25*256,z*256,(7+(int)(h%5))*256,wMix(0x347769,0x94ad7b,(int)(h%350)));
    }
    for(int x=-15;x<=15;x++) {
        int32_t y=27*256-x*x*256/130;
        wBox(c,x*256,y,24*256,110,70,2*256,0x988369);
        if(x%3==0) {
            wLine(c,wP(x*256,y,22*256),wP(x*256,y+3*256,22*256),0xb9a785,1000);
            wLine(c,wP(x*256,y,26*256),wP(x*256,y+3*256,26*256),0xb9a785,1000);
        }
    }
}

static int32_t wTerrain(int32_t x,int32_t z) {
    int32_t ridge=(wWave(x*9+z*3)+1000)*7/1000+(wWave(z*13-x*3)+1000)*4/1000;
    int32_t trench=clampI(15-(x<0?-x:x),0,15);return(-18+ridge-trench/2)*256;
}
static int32_t wRoadX(int32_t zQ8) { return wWave((int64_t)zQ8*6/256)*23*256/1000; }
static int32_t wRoadY(int32_t zQ8) { return 6*256+wWave((int64_t)zQ8*2/256)*5*256/1000; }
static void wLandscape(Art *c,int road) {
    const int32_t *v=c->config->world;
    uint32_t sand=v[NR_WORLD_ACCENT]?(uint32_t)v[NR_WORLD_ACCENT]:0xb48672;
    for(int z=60;z>-64;z-=4)for(int x=-60;x<64;x+=4) {
        WPoint a=wP(x*256,wTerrain(x,z),z*256),b=wP((x+4)*256,wTerrain(x+4,z),z*256);
        WPoint d=wP((x+4)*256,wTerrain(x+4,z-4),(z-4)*256),e=wP(x*256,wTerrain(x,z-4),(z-4)*256);
        int sh=clampI(450+(a.y+18*256)/14+(a.y-b.y)/9+(a.y-e.y)/10,240,840);
        uint32_t co=wMix(0x292e4b,sand,sh);
        wTriangle(c,a,b,d,co,1000);wTriangle(c,a,d,e,wShade(co,940),1000);
        if(x==-60)wQuad(c,a,e,wP(e.x,-32*256,e.z),wP(a.x,-32*256,a.z),wShade(co,450),1000);
        if(x==60)wQuad(c,b,d,wP(d.x,-32*256,d.z),wP(b.x,-32*256,b.z),wShade(co,380),1000);
        if(z==-60)wQuad(c,e,d,wP(d.x,-32*256,d.z),wP(e.x,-32*256,e.z),wShade(co,460),1000);
    }
    if(!road) {
        for(int z=-60;z<60;z++) {
            int32_t x=wWave(z*5)*6*256/1000,y=wTerrain(x/256,z)+50;
            wQuad(c,wP(x-3*256,y,z*256),wP(x+3*256,y,z*256),
                wP(x+3*256,y,(z+2)*256),wP(x-3*256,y,(z+2)*256),
                wMix(0x255361,0x9ac7b8,(wWave((int64_t)z*34-(int64_t)c->time/11)+1000)/6),1000);
        }
        return;
    }
    int64_t travel=v[NR_WORLD_TRAVEL];
    for(int z=-62;z<62;z+=2) {
        int32_t z1=z*256,z2=(z+2)*256,x1=wRoadX(z1),x2=wRoadX(z2),y1=wRoadY(z1),y2=wRoadY(z2);
        WPoint a=wP(x1-6*256,y1,z1),b=wP(x1+6*256,y1,z1),d=wP(x2+6*256,y2,z2),e=wP(x2-6*256,y2,z2);
        wQuad(c,a,b,d,e,0x343f51,1000);
        wQuad(c,a,e,wP(e.x,e.y-512,e.z),wP(a.x,a.y-512,a.z),0x798081,1000);
        wQuad(c,b,d,wP(d.x,d.y-512,d.z),wP(b.x,b.y-512,b.z),0x42475b,1000);
        for(int side=-1;side<=1;side+=2) {
            wLine(c,wP(x1+side*5*256,y1+40,z1),wP(x2+side*5*256,y2+40,z2),0xdfbc9c,1000);
            if(z%8==0) {
                wLine(c,wP(x1+side*6*256,y1,z1),wP(x1+side*6*256,y1+2*256,z1),0xc7b6a6,1000);
                wDot(c,wP(x1+side*6*256,y1+2*256,z1),side<0?0xe6d7a8:0xbe887c,900,0);
            }
        }
        if(z%16==0)for(int side=-1;side<=1;side+=2)
            wBox(c,x1+side*4*256,y1-512,z1,180,
                 y1-512-wTerrain((x1+side*4*256)/256,z),180,0x5b6874);
    }
    for(int d=0;d<11;d++) {
        int32_t z1=modI((int64_t)d*12*256-travel,132*256)-66*256,z2=z1+5*256;
        if(z1 < -62*256 || z2>62*256)continue;
        int32_t x1=wRoadX(z1),x2=wRoadX(z2),y1=wRoadY(z1)+48,y2=wRoadY(z2)+48;
        wQuad(c,wP(x1-60,y1,z1),wP(x1+60,y1,z1),wP(x2+60,y2,z2),wP(x2-60,y2,z2),0xe9d9a5,1000);
    }
}

static WPoint wDiscPoint(int32_t r,int32_t angle,int32_t tilt,int32_t height) {
    int32_t x=wCos(angle)*r/1000,z=wSin(angle)*r/1000;
    return wP(x,height+wSin(tilt)*z/1000,wCos(tilt)*z/1000);
}
static void wAccretion(Art *c) {
    const int32_t *v=c->config->world;int tilt=v[NR_WORLD_DISC_TILT];
    int32_t time=(int32_t)(c->time%7200000);
    uint32_t gold=v[NR_WORLD_ACCENT]?(uint32_t)v[NR_WORLD_ACCENT]:0xebbb7a;
    for(int lat=-90;lat<90;lat+=10)for(int lon=0;lon<360;lon+=10) {
        WPoint p[4];int aa[4]={lat,lat,lat+10,lat+10},bb[4]={lon,lon+10,lon+10,lon};
        for(int k=0;k<4;k++) {
            int32_t r=wCos(aa[k]*256)*9*256/1000;
            p[k]=wP(wCos(bb[k]*256)*r/1000,wSin(aa[k]*256)*9*256/1000,wSin(bb[k]*256)*r/1000);
        }
        wQuad(c,p[0],p[1],p[2],p[3],0x07090f,1000);
    }
    int segments=v[NR_WORLD_DETAIL]==2?192:(v[NR_WORLD_DETAIL]==1?128:80);
    for(int ring=0;ring<25;ring++) {
        int32_t r=10*256+ring*310,outer=r+310;
        for(int j=0;j<segments;j++) {
            int32_t a=j*360*256/segments,b=(j+1)*360*256/segments;
            int wave=wSin((int64_t)a*2-ring*6800-(int64_t)time*2);
            int bright=clampI(930-ring*24+wave/8,150,1000);uint32_t co=wMix(0x61304c,gold,bright);
            int32_t radialVelocity=(-wSin(a)*c->sy+wCos(a)*wSin(tilt)/1000*c->sp+
                wCos(a)*wCos(tilt)/1000*c->cy*c->cp/1000)/1000;
            int recede=clampI((radialVelocity+1000)/2,0,1000);
            co=wMix(co,0xcc593f,recede*v[NR_WORLD_REDSHIFT]/1300);
            co=wMix(co,0xe5e8ff,(1000-recede)*v[NR_WORLD_REDSHIFT]/2400);
            wQuad(c,wDiscPoint(r,a,tilt,0),wDiscPoint(outer,a,tilt,0),
                wDiscPoint(outer,b,tilt,0),wDiscPoint(r,b,tilt,0),wShade(co,bright),1000);
        }
    }
    for(int n=0;n<520;n++) {
        uint32_t h=hashI((uint32_t)n*1297u+(uint32_t)v[NR_WORLD_SEED]);
        int age=(int)((c->time+(h%18000))%18000);
        int32_t radius=50*256-age*40*256/18000;
        int32_t angular=(int32_t)(h%(360*256))+age*5+(int32_t)((int64_t)age*(50*256-radius)/1024);
        WPoint p=wDiscPoint(radius,angular,tilt,(int32_t)(h%180)-90);
        int alpha=clampI(age*3,0,1000);alpha=clampI((18000-age)*2,0,alpha);
        wDot(c,p,wMix(gold,0xf5e7d0,(int)(h%600)),alpha,0);
        if(n%2==0)wLine(c,wDiscPoint(radius+24,angular-700,tilt,0),p,wShade(gold,700),alpha*3/4);
    }
    for(int a=0;a<360*256;a+=256)wDot(c,wDiscPoint(10*256,a,tilt,30),0xf3dfad,950,0);
}

static int32_t wOceanY(int x,int z,int64_t t) {
    return (wWave((int64_t)x*15+z*5-t/8)*190+wWave((int64_t)z*23-x*7+t/11)*95)/1000;
}
static WPoint wOceanDetailPoint(const Art *c,int x,int z,int64_t t) {
    const int32_t *d=c->config->detail;
    const int angle[5]={0,71,-39,127,19},weight[5]={1000,480,260,160,110};
    const int frequency[5]={1000,1340,2130,2710,630},rate[5]={1000,850,690,530,1280};
    int64_t yy=0,xx=0,zz=0;
    for(int k=0;k<5;k++) {
        int32_t a=d[NR_WORLD_DETAIL_WIND_ANGLE]+angle[k]*256,sn=wSin(a),cs=wCos(a);
        int32_t amplitude=(int32_t)((int64_t)d[NR_WORLD_DETAIL_WAVE_HEIGHT]*weight[k]/2010);
        if(k)amplitude=(int32_t)((int64_t)amplitude*d[NR_WORLD_DETAIL_CROSS_SWELL]/480);
        int64_t distance=((int64_t)x*cs+(int64_t)z*sn)*256/1000;
        int64_t phase=distance*1024*frequency[k]/d[NR_WORLD_DETAIL_WAVELENGTH]/1000-
                      t*rate[k]/8000;
        int32_t si=wWave(phase),co=wWave(phase+256);
        yy+=(int64_t)si*amplitude/1000;
        xx+=(int64_t)co*amplitude*d[NR_WORLD_DETAIL_CHOPPINESS]/1000*cs/1000000;
        zz+=(int64_t)co*amplitude*d[NR_WORLD_DETAIL_CHOPPINESS]/1000*sn/1000000;
    }
    return wP(x*256+(int32_t)xx,(int32_t)yy,z*256+(int32_t)zz);
}
static void wOcean(Art *c) {
    const int32_t *v=c->config->world;int64_t t=(int64_t)(c->time%3600000)*v[NR_WORLD_FLOW]/1000;
    if(c->hasDetail)t=t*c->config->detail[NR_WORLD_DETAIL_WAVE_SPEED]/1000;
    uint32_t teal=v[NR_WORLD_ACCENT]?(uint32_t)v[NR_WORLD_ACCENT]:0x79bcb8;
    for(int z=60;z>-60;z-=2)for(int x=-60;x<60;x+=2) {
        WPoint a,b,d,e;
        if(c->hasDetail) {
            a=wOceanDetailPoint(c,x,z,t);b=wOceanDetailPoint(c,x+2,z,t);
            d=wOceanDetailPoint(c,x+2,z-2,t);e=wOceanDetailPoint(c,x,z-2,t);
        } else {
            a=wP(x*256,wOceanY(x,z,t),z*256);b=wP((x+2)*256,wOceanY(x+2,z,t),z*256);
            d=wP((x+2)*256,wOceanY(x+2,z-2,t),(z-2)*256);e=wP(x*256,wOceanY(x,z-2,t),(z-2)*256);
        }
        int light=150+clampI(a.y+200,0,400);uint32_t co=wMix(0x142c40,teal,light);
        wTriangle(c,a,b,d,co,1000);wTriangle(c,a,d,e,wShade(co,850),1000);
        if(a.y>235)wLine(c,a,b,0xc5dbca,c->hasDetail?c->config->detail[NR_WORLD_DETAIL_FOAM]:800);
    }
    for(int i=0;i<7;i++) {
        int x=25+i*2,z=15+i;
        wBox(c,x*256,(7+(i%3)*3)*256,z*256,3*256,12*256,4*256,
             wMix(0x283345,0x8b8980,i*70));
    }
    wLine(c,wV(-12,0,-10),wV(-12,21,-10),0xb7c7c2,1000);
    wTriangle(c,wV(-12,20,-10),wV(-12,3,-10),wV(-3,3,-10),0xcfbfad,1000);
    wTriangle(c,wV(-13,15,-10),wV(-13,3,-10),wV(-20,3,-10),0x8199b2,1000);
    wBox(c,-12*256,128,-10*256,7*256,2*256,2*256,0x796c65);
}

int nrScenicArtValidate(const NrScenicArtConfig *config) {
    if(!config||config->hasWorldDetail>1)return 0;
    for(int i=0;i<NR_WORLD_FIELD_COUNT;i++) {
        /* RC4 viewport allocation has no scene-art-specific width/height cap. */
        if(i==NR_WORLD_WIDTH||i==NR_WORLD_HEIGHT) {
            if(config->world[i]<0)return 0;
        } else if(config->world[i]<WORLD_MIN[i]||config->world[i]>WORLD_MAX[i])return 0;
    }
    for(int i=0;i<NR_WORLD_DETAIL_FIELD_COUNT;i++)
        if(config->detail[i]<WDETAIL_MIN[i]||config->detail[i]>WDETAIL_MAX[i])return 0;
    return config->world[NR_WORLD_SCENE]>=NR_SCENIC_PEARL_CASCADE&&
           config->world[NR_WORLD_SCENE]<=NR_SCENIC_SILT;
}
int nrScenicArtValidateView(const NrScenicArtConfig *config) {
    if(!config)return 0;
    /* Validate every authored/non-camera value in its exact source domain.
       Only replace the eight values supplied from the canonical RC4 camera
       while asking the strict validator to check the remaining 16+8 fields. */
    NrScenicArtConfig authored=*config;
    authored.world[NR_WORLD_CAMERA_X]=-68*256;
    authored.world[NR_WORLD_CAMERA_Y]=48*256;
    authored.world[NR_WORLD_CAMERA_Z]=-96*256;
    authored.world[NR_WORLD_YAW]=35*256;
    authored.world[NR_WORLD_PITCH]=-22*256;
    authored.world[NR_WORLD_ROLL]=0;
    authored.world[NR_WORLD_FOV]=62*256;
    authored.world[NR_WORLD_SPAN]=145*256;
    if(!nrScenicArtValidate(&authored))return 0;

    const int32_t *v=config->world;
    if(v[NR_WORLD_CAMERA_X]<-25600000||v[NR_WORLD_CAMERA_X]>25600000||
       v[NR_WORLD_CAMERA_Y]<-25600000||v[NR_WORLD_CAMERA_Y]>25600000||
       v[NR_WORLD_CAMERA_Z]<-25600000||v[NR_WORLD_CAMERA_Z]>25600000||
       v[NR_WORLD_YAW]<-9216000||v[NR_WORLD_YAW]>9216000||
       v[NR_WORLD_PITCH]<-23014||v[NR_WORLD_PITCH]>23014||
       v[NR_WORLD_ROLL]<-9216000||v[NR_WORLD_ROLL]>9216000||
       v[NR_WORLD_FOV]<2560||v[NR_WORLD_FOV]>38400||
       v[NR_WORLD_SPAN]<26||v[NR_WORLD_SPAN]>512000||
       v[NR_WORLD_PROJECTION]<0||v[NR_WORLD_PROJECTION]>1)return 0;
    return 1;
}
int nrScenicArtDraw(const NrScenicArtConfig *config,uint64_t timeMs,const NrScenicArtSink *sink) {
    if(!nrScenicArtValidateView(config)||timeMs>UINT64_C(9007199254740991)||!sink||
       !sink->triangle||!sink->line||!sink->point)return 0;
    Art c={config,sink,timeMs,config->hasWorldDetail,0,0,0,0};
    c.sy=wSin(config->world[NR_WORLD_YAW]);c.cy=wCos(config->world[NR_WORLD_YAW]);
    c.sp=wSin(config->world[NR_WORLD_PITCH]);c.cp=wCos(config->world[NR_WORLD_PITCH]);
    switch(config->world[NR_WORLD_SCENE]) {
        case NR_SCENIC_PEARL_CASCADE:wWaterfall(&c);break;
        case NR_SCENIC_COPPER_CAUSEWAY:wLandscape(&c,1);break;
        case NR_SCENIC_RED_SHIFT:wAccretion(&c);break;
        case NR_SCENIC_TIDAL_GLASS:wOcean(&c);break;
        case NR_SCENIC_SILT:wLandscape(&c,0);break;
        default:return 0;
    }
    return 1;
}
