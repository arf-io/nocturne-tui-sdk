/* Exact RC2 source projection and sample traversal, without framebuffer state. */
#include "scenic_source_raster.h"

#include <limits.h>
#include <stddef.h>

#include "../../src/world_fields.inc"
#include "../../src/sine.inc"

typedef struct { int32_t x,y,z; } SourcePoint;
typedef struct { int32_t x,y,z; } SourceScreen;

static int32_t modSource(int64_t value,int32_t divisor) {
    int32_t remainder=(int32_t)(value%divisor);
    return remainder<0?remainder+divisor:remainder;
}
static int32_t sourceSinTable(int64_t phase) {
    return SINE[modSource(phase,1024)];
}
static int32_t sourceSin(int64_t angle) {
    int32_t q=modSource(angle,360*256);
    int64_t phase=(int64_t)q*1024;
    int32_t k=(int32_t)(phase/(360*256));
    int32_t remainder=(int32_t)(phase%(360*256));
    return sourceSinTable(k)+(int32_t)((int64_t)(sourceSinTable(k+1)-sourceSinTable(k))*remainder/(360*256));
}
static int32_t sourceCos(int64_t angle) { return sourceSin(angle+90*256); }
static int32_t clampSource(int32_t value,int32_t low,int32_t high) {
    return value<low?low:(value>high?high:value);
}

static SourcePoint sourceCamera(const NrScenicSourceRaster *r,SourcePoint p) {
    const int32_t *v=r->config.world;
    int64_t x=(int64_t)p.x-v[NR_WORLD_CAMERA_X];
    int64_t y=(int64_t)p.y-v[NR_WORLD_CAMERA_Y];
    int64_t z=(int64_t)p.z-v[NR_WORLD_CAMERA_Z];
    int64_t a=(x*r->cosYaw-z*r->sinYaw)/1000;
    int64_t b=(x*r->sinYaw+z*r->cosYaw)/1000;
    int64_t u=(y*r->cosPitch-b*r->sinPitch)/1000;
    int64_t d=(y*r->sinPitch+b*r->cosPitch)/1000;
    SourcePoint result={
        (int32_t)((a*r->cosRoll+u*r->sinRoll)/1000),
        (int32_t)((u*r->cosRoll-a*r->sinRoll)/1000),
        (int32_t)d
    };
    return result;
}
static SourceScreen sourceProject(const NrScenicSourceRaster *r,SourcePoint p) {
    SourceScreen s;s.z=p.z;
    if(r->orthographic) {
        int32_t span=r->config.world[NR_WORLD_SPAN];
        s.x=r->sampleWidth*8+(int32_t)((int64_t)p.x*r->sampleWidth*16/span);
        s.y=r->sampleHeight*8-(int32_t)((int64_t)p.y*r->sampleWidth*16/span);
    } else {
        s.x=r->sampleWidth*8+(int32_t)((int64_t)p.x*r->focal/p.z);
        s.y=r->sampleHeight*8-(int32_t)((int64_t)p.y*r->focal/p.z);
    }
    return s;
}
static int32_t sourceDepth(const NrScenicSourceRaster *r,int32_t z) {
    return r->orthographic?268435456-z:(1<<26)/z;
}
static int64_t sourceEdge(SourceScreen a,SourceScreen b,int32_t x,int32_t y) {
    return (int64_t)(x-a.x)*(b.y-a.y)-(int64_t)(y-a.y)*(b.x-a.x);
}
static void emit(const NrScenicSourceRaster *r,int32_t x,int32_t y,int32_t z,
                 uint32_t rgb,int32_t alpha,int32_t threshold) {
    r->coverage(r->coverageUser,x,y,z,rgb,alpha,threshold);
}

static void rasterTriangle(NrScenicSourceRaster *r,SourcePoint a,SourcePoint b,
                           SourcePoint c,uint32_t rgb,int32_t alpha) {
    SourceScreen p=sourceProject(r,a),q=sourceProject(r,b),s=sourceProject(r,c);
    int64_t area=sourceEdge(p,q,s.x,s.y);
    if(!area)return;
    if(area<0){SourceScreen t=q;q=s;s=t;area=-area;}
    int32_t minX=p.x<q.x?(p.x<s.x?p.x:s.x):(q.x<s.x?q.x:s.x);
    int32_t maxX=p.x>q.x?(p.x>s.x?p.x:s.x):(q.x>s.x?q.x:s.x);
    int32_t minY=p.y<q.y?(p.y<s.y?p.y:s.y):(q.y<s.y?q.y:s.y);
    int32_t maxY=p.y>q.y?(p.y>s.y?p.y:s.y):(q.y>s.y?q.y:s.y);
    int32_t x0=clampSource(minX/16,0,r->sampleWidth-1);
    int32_t x1=clampSource(maxX/16+1,0,r->sampleWidth-1);
    int32_t y0=clampSource(minY/16,0,r->sampleHeight-1);
    int32_t y1=clampSource(maxY/16+1,0,r->sampleHeight-1);
    int32_t ip=sourceDepth(r,p.z),iq=sourceDepth(r,q.z),is=sourceDepth(r,s.z);
    for(int32_t y=y0;y<=y1;y++)for(int32_t x=x0;x<=x1;x++) {
        int64_t e0=sourceEdge(q,s,x*16+8,y*16+8);
        int64_t e1=sourceEdge(s,p,x*16+8,y*16+8);
        int64_t e2=sourceEdge(p,q,x*16+8,y*16+8);
        if(e0<0||e1<0||e2<0)continue;
        int32_t z=(int32_t)((e0*ip+e1*iq+e2*is)/area);
        emit(r,x,y,z,rgb,alpha,750);
    }
}

static int64_t sourcePlane(const NrScenicSourceRaster *r,SourcePoint p,int plane) {
    if(plane==0)return (int64_t)p.z-384;
    const int32_t *v=r->config.world;
    if(r->orthographic) {
        int64_t half=v[NR_WORLD_SPAN]/2;
        switch(plane) {
            case 1:return (int64_t)p.x+half;
            case 2:return half-p.x;
            case 3:return (int64_t)p.y*r->sampleWidth+half*r->sampleHeight;
            default:return half*r->sampleHeight-(int64_t)p.y*r->sampleWidth;
        }
    }
    switch(plane) {
        case 1:return (int64_t)p.x*r->focal+(int64_t)p.z*r->sampleWidth*8;
        case 2:return (int64_t)p.z*r->sampleWidth*8-(int64_t)p.x*r->focal;
        case 3:return (int64_t)p.y*r->focal+(int64_t)p.z*r->sampleHeight*8;
        default:return (int64_t)p.z*r->sampleHeight*8-(int64_t)p.y*r->focal;
    }
}
static SourcePoint sourceIntersection(SourcePoint u,SourcePoint v,int64_t du,int64_t dv) {
    int64_t t=du*65536/(du-dv);
    SourcePoint p={
        u.x+(int32_t)(((int64_t)v.x-u.x)*t/65536),
        u.y+(int32_t)(((int64_t)v.y-u.y)*t/65536),
        u.z+(int32_t)(((int64_t)v.z-u.z)*t/65536)
    };
    return p;
}
static void rasterClippedTriangle(NrScenicSourceRaster *r,SourcePoint a,
                                  SourcePoint b,SourcePoint c,uint32_t rgb,
                                  int32_t alpha) {
    SourcePoint p[12],q[12];p[0]=sourceCamera(r,a);p[1]=sourceCamera(r,b);p[2]=sourceCamera(r,c);
    int count=3;
    for(int plane=0;plane<5&&count>=3;plane++) {
        int n=0;
        for(int i=0;i<count;i++) {
            SourcePoint u=p[i],v=p[(i+1)%count];
            int64_t du=sourcePlane(r,u,plane),dv=sourcePlane(r,v,plane);
            if(du>=0&&n<12)q[n++]=u;
            if((du>=0)!=(dv>=0)&&n<12)q[n++]=sourceIntersection(u,v,du,dv);
        }
        count=n;for(int i=0;i<n;i++)p[i]=q[i];
    }
    if(count>=3)for(int i=1;i<count-1;i++)
        if(p[0].z>=384&&p[i].z>=384&&p[i+1].z>=384)
            rasterTriangle(r,p[0],p[i],p[i+1],rgb,alpha);
}

static void rasterPoint(NrScenicSourceRaster *r,SourcePoint p,uint32_t rgb,
                        int32_t alpha,int32_t radius) {
    p=sourceCamera(r,p);
    for(int plane=0;plane<5;plane++)if(sourcePlane(r,p,plane)<0)return;
    SourceScreen s=sourceProject(r,p);
    int32_t cx=s.x/16,cy=s.y/16,depth=sourceDepth(r,p.z);
    for(int32_t y=cy-radius;y<=cy+radius;y++)for(int32_t x=cx-radius;x<=cx+radius;x++) {
        if(x<0||y<0||x>=r->sampleWidth||y>=r->sampleHeight)continue;
        if(radius&&(x-cx)*(x-cx)+(y-cy)*(y-cy)>radius*radius)continue;
        emit(r,x,y,depth,rgb,alpha,950);
    }
}
static void rasterLine(NrScenicSourceRaster *r,SourcePoint a,SourcePoint b,
                       uint32_t rgb,int32_t alpha) {
    SourcePoint u=sourceCamera(r,a),v=sourceCamera(r,b);
    for(int plane=0;plane<5;plane++) {
        int64_t a0=sourcePlane(r,u,plane),b0=sourcePlane(r,v,plane);
        if(a0<0&&b0<0)return;
        if((a0>=0)!=(b0>=0)) {
            SourcePoint p=sourceIntersection(u,v,a0,b0);
            if(a0<0)u=p;else v=p;
        }
    }
    if(u.z<384||v.z<384)return;
    SourceScreen p=sourceProject(r,u),q=sourceProject(r,v);
    int32_t dx=q.x-p.x,dy=q.y-p.y;
    int32_t ax=dx<0?-dx:dx,ay=dy<0?-dy:dy;
    int32_t n=clampSource((ax>ay?ax:ay)/12+1,1,2048);
    for(int32_t k=0;k<=n;k++) {
        int32_t x=(int32_t)(p.x+(int64_t)dx*k/n)/16;
        int32_t y=(int32_t)(p.y+(int64_t)dy*k/n)/16;
        if(x<0||y<0||x>=r->sampleWidth||y>=r->sampleHeight)continue;
        int32_t z=(int32_t)(((int64_t)sourceDepth(r,u.z)*(n-k)+
                             (int64_t)sourceDepth(r,v.z)*k)/n);
        emit(r,x,y,z,rgb,alpha,950);
    }
}
static void sinkTriangle(void *user,int32_t ax,int32_t ay,int32_t az,
                         int32_t bx,int32_t by,int32_t bz,
                         int32_t cx,int32_t cy,int32_t cz,uint32_t rgb,int32_t alpha) {
    NrScenicSourceRaster *r=(NrScenicSourceRaster *)user;
    rasterClippedTriangle(r,(SourcePoint){ax,ay,az},(SourcePoint){bx,by,bz},
                          (SourcePoint){cx,cy,cz},rgb,alpha);
}
static void sinkLine(void *user,int32_t ax,int32_t ay,int32_t az,
                     int32_t bx,int32_t by,int32_t bz,uint32_t rgb,int32_t alpha) {
    rasterLine((NrScenicSourceRaster *)user,(SourcePoint){ax,ay,az},
               (SourcePoint){bx,by,bz},rgb,alpha);
}
static void sinkPoint(void *user,int32_t x,int32_t y,int32_t z,uint32_t rgb,
                      int32_t alpha,int32_t radius) {
    rasterPoint((NrScenicSourceRaster *)user,(SourcePoint){x,y,z},rgb,alpha,radius);
}

int nrScenicSourceRasterInit(NrScenicSourceRaster *r,const NrScenicArtConfig *config,
    int32_t outputWidth,int32_t outputHeight,NrScenicSourceCoverageSink coverage,
    void *coverageUser) {
    if(!r||!config||!coverage||outputWidth<=0||outputHeight<=0||!nrScenicArtValidateView(config))return 0;
    int32_t sx=config->world[NR_WORLD_SAMPLING]?2:1;
    int32_t sy=config->world[NR_WORLD_SAMPLING]?4:2;
    if(outputWidth>INT32_MAX/sx||outputHeight>INT32_MAX/sy)return 0;
    int32_t sampleWidth=outputWidth*sx,sampleHeight=outputHeight*sy;
    if(sampleWidth>INT32_MAX/16||sampleHeight>INT32_MAX/16)return 0;
    r->config=*config;
    r->outputWidth=outputWidth;r->outputHeight=outputHeight;
    r->sampleWidth=sampleWidth;r->sampleHeight=sampleHeight;
    r->orthographic=config->world[NR_WORLD_PROJECTION]!=0;
    const int32_t *v=r->config.world;
    r->sinYaw=sourceSin(v[NR_WORLD_YAW]);r->cosYaw=sourceCos(v[NR_WORLD_YAW]);
    r->sinPitch=sourceSin(v[NR_WORLD_PITCH]);r->cosPitch=sourceCos(v[NR_WORLD_PITCH]);
    r->sinRoll=sourceSin(v[NR_WORLD_ROLL]);r->cosRoll=sourceCos(v[NR_WORLD_ROLL]);
    r->focal=0;
    if(!r->orthographic) {
        int32_t sine=sourceSin(v[NR_WORLD_FOV]/2);
        if(!sine)return 0;
        int64_t focal=(int64_t)sampleWidth*8*sourceCos(v[NR_WORLD_FOV]/2)/sine;
        if(focal<=0||focal>INT32_MAX)return 0;
        r->focal=(int32_t)focal;
    }
    r->coverage=coverage;r->coverageUser=coverageUser;
    r->primitives=(NrScenicArtSink){r,sinkTriangle,sinkLine,sinkPoint};
    return 1;
}
const NrScenicArtSink *nrScenicSourceRasterSink(NrScenicSourceRaster *r) {
    return r?&r->primitives:NULL;
}
int nrScenicSourceRasterProjectPoint(const NrScenicSourceRaster *r,
    int32_t worldX,int32_t worldY,int32_t worldZ,int32_t *cameraX,
    int32_t *cameraY,int32_t *cameraZ,int32_t *screenX16,int32_t *screenY16,
    int32_t *encodedDepth) {
    if(!r||!cameraX||!cameraY||!cameraZ||!screenX16||!screenY16||!encodedDepth)return 0;
    SourcePoint p=sourceCamera(r,(SourcePoint){worldX,worldY,worldZ});
    if(p.z<384)return 0;
    SourceScreen s=sourceProject(r,p);
    *cameraX=p.x;*cameraY=p.y;*cameraZ=p.z;*screenX16=s.x;*screenY16=s.y;
    *encodedDepth=sourceDepth(r,p.z);return 1;
}
