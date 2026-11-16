#include "internal.h"
#include "tables.inc"
double nrClamp(double v,double l,double h) {
    return v<l?l:v>h?h:v;
}
double nrAbs(double x) {
    return x<0?-x:x;
}
double nrFloor(double x) {
    int64_t i=(int64_t)x;
    return i-(x<i);
}
double nrSin(double d) {
    double p=d/360.0;
    p-=nrFloor(p);
    p*=4096;
    int i=(int)p;
    return (SIN_Q30[i]+(SIN_Q30[i+1]-(double)SIN_Q30[i])*(p-i))/1073741824.0;
}
double nrCos(double d) {
    return nrSin(d+90);
}
double nrSqrt(double v) {
    if(v<=0)return 0;
    uint64_t bits;
    memcpy(&bits,&v,8);
    bits=(bits>>1)+0x1ff8000000000000ull;
    double r;
    memcpy(&r,&bits,8);
    for(int i=0; i<7; i++)r=(r+v/r)*.5;
    return r;
}
double nrEase(double p,int e) {
    p=nrClamp(p,0,1);
    switch(e) {
        case 1:return p*p;
        case 2:return 1-(1-p)*(1-p);
        case 3:return p*p*(3-2*p);
        case 4:return p*p*p*(p*(p*6-15)+10);
        case 5:return .5-.5*nrCos(p*180);
        case 6:return p>=1?1:0;
        default:return p;
    }
}
uint32_t nrHash(uint32_t x) {
    x^=x>>16;
    x*=0x7feb352du;
    x^=x>>15;
    x*=0x846ca68bu;
    return x^(x>>16);
}
double nrRandom(uint32_t s,uint32_t i,uint32_t p) {
    return (nrHash(s^(i*0x9e3779b9u)^(p*0x85ebca6bu))>>8)/16777216.0;
}
Vec3 nrV(double x,double y,double z) {
    Vec3 v= {
        x,y,z
    };
    return v;
}
Vec3 nrAdd(Vec3 a,Vec3 b) {
    return nrV(a.x+b.x,a.y+b.y,a.z+b.z);
}
Vec3 nrSub(Vec3 a,Vec3 b) {
    return nrV(a.x-b.x,a.y-b.y,a.z-b.z);
}
Vec3 nrScale(Vec3 a,double b) {
    return nrV(a.x*b,a.y*b,a.z*b);
}
double nrDot(Vec3 a,Vec3 b) {
    return a.x*b.x+a.y*b.y+a.z*b.z;
}
Vec3 nrCross(Vec3 a,Vec3 b) {
    return nrV(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);
}
Vec3 nrNormal(Vec3 v) {
    double l=nrSqrt(nrDot(v,v));
    return l>1e-12?nrScale(v,1/l):nrV(0,1,0);
}
static int32_t q(double v) {
    v=nrClamp(v,-32760,32760)*NR_Q;
    return (int32_t)(v+(v<0?-.5:.5));
}
QVec3 nrQuantize(Vec3 v) {
    QVec3 r= {
        q(v.x),q(v.y),q(v.z)
    };
    return r;
}
Vec3 nrUnquantize(QVec3 v) {
    return nrV(v.x/NR_Q,v.y/NR_Q,v.z/NR_Q);
}
void nrBasis(const Camera*c,Vec3*r,Vec3*u,Vec3*f) {
    double cy=nrCos(c->yaw),sy=nrSin(c->yaw),cp=nrCos(c->pitch),sp=nrSin(c->pitch),cr=nrCos(c->roll),sr=nrSin(c->roll);
    *f=nrV(sy*cp,sp,-cy*cp);
    Vec3 a=nrV(cy,0,sy),b=nrV(-sy*sp,cp,cy*sp);
    *r=nrAdd(nrScale(a,cr),nrScale(b,sr));
    *u=nrAdd(nrScale(b,cr),nrScale(a,-sr));
}
double nrTrack(const Track*t,uint64_t us,double idx) {
    double base=t->initial+t->step*idx,range=t->max-t->min;
    if(range<=0)return t->min;
    double travel=t->rate*(double)us/(double)(t->periodUs?t->periodUs:1000000),v=(base+travel-t->min)/range;
    if(t->boundary==1)v-=nrFloor(v);
    else if(t->boundary==2) {
        v-=2*nrFloor(v/2);
        if(v>1)v=2-v;
    }
    else if(t->boundary>=3) {
        double a=nrFloor(v),f=v-a;
        uint32_t k=(uint32_t)(int64_t)a;
        v=nrRandom(t->seed,k,1);
        if(t->boundary==4)v+=(nrRandom(t->seed,k+1,1)-v)*nrEase(f,3);
    }
    else v=nrClamp(v,0,1);
    return t->min+range*nrEase(v,t->easing);
}
uint32_t nrRgb(double r,double g,double b) {
    return ((uint32_t)(nrClamp(r,0,1)*255+.5)<<16)|((uint32_t)(nrClamp(g,0,1)*255+.5)<<8)|(uint32_t)(nrClamp(b,0,1)*255+.5);
}
uint32_t nrMix(uint32_t a,uint32_t b,double t) {
    t=nrClamp(t,0,1);
    uint32_t o=0;
    for(int k=0; k<3; k++) {
        int shift=k*8;
        double x=(a>>shift)&255,y=(b>>shift)&255;
        o|=(uint32_t)(x+(y-x)*t+.5)<<shift;
    }
    return o;
}
static int gammaByte(double c) {
    c=nrClamp(c,0,1);
    int lo=0,hi=255;
    while(lo<hi) {
        int mid=(lo+hi)/2;
        if(c>(SRGB_LINEAR[mid]+SRGB_LINEAR[mid+1])*.5)lo=mid+1;
        else hi=mid;
    }
    return lo;
}
static Vec3 labLinear(double L,double a,double b) {
    double l=L+.3963377774*a+.2158037573*b,m=L-.1055613458*a-.0638541728*b,s=L-.0894841775*a-1.291485548*b;
    l=l*l*l;
    m=m*m*m;
    s=s*s*s;
    return nrV(4.0767416621*l-3.3077115913*m+.2309699292*s,-1.2684380046*l+2.6097574011*m-.3413193965*s,-.0041960863*l-.7034186147*m+1.707614701*s);
}
static int inGamut(Vec3 v) {
    return v.x>=0&&v.x<=1&&v.y>=0&&v.y<=1&&v.z>=0&&v.z<=1;
}
uint32_t nrLabColor(double L,double a,double b) {
    Vec3 v=labLinear(L,a,b);
    if(!inGamut(v)) {
        double lo=0,hi=1;
        for(int i=0; i<16; i++) {
            double mid=(lo+hi)/2;
            if(inGamut(labLinear(L,a*mid,b*mid)))lo=mid;
            else hi=mid;
        }
        v=labLinear(L,a*lo,b*lo);
    }
    return (uint32_t)gammaByte(v.x)<<16|(uint32_t)gammaByte(v.y)<<8|(uint32_t)gammaByte(v.z);
}
uint32_t nrOklch(int32_t l,int32_t c,int32_t h) {
    if(l<0||l>1000000||c<0||c>500000||h<-36000000||h>36000000)return 0xffffffffu;
    if(!l)return 0;
    if(l==1000000)return 0xffffffu;
    return nrLabColor(l/1e6,c/1e6*nrCos(h/1000.0),c/1e6*nrSin(h/1000.0));
}
void nrInitMaterial(Material*m,int id) {
    memset(m,0,sizeof(*m));
    m->used=1;
    m->spacing=1;
    m->alpha=(Track) {
        1,0,0,1,0,1000000,0,0,1
    };
    for(int k=0; k<4; k++)m->channel[k]=(Track) {
        0,0,0,1,0,1000000,0,0,1
    };
    m->channel[0].initial=.76;
    m->channel[1].initial=.08;
    m->channel[1].max=.5;
    m->channel[2].initial=id==1?55:id==2?190:290;
    m->channel[2].max=360;
    m->channel[2].boundary=1;
    m->index=(Track) {
        0,0,0,1,0,1000000,1,0,1
    };
}
static uint32_t colorSpace(int space,double v[4]) {
    if(space==0)return nrLabColor(v[0],v[1]*nrCos(v[2]),v[1]*nrSin(v[2]));
    if(space==1)return nrLabColor(v[0],v[1],v[2]);
    if(space==4)return nrRgb(v[0],v[1],v[2]);
    if(space==5)return gammaByte(v[0])<<16|gammaByte(v[1])<<8|gammaByte(v[2]);
    if(space==6)return nrRgb((1-v[0])*(1-v[3]),(1-v[1])*(1-v[3]),(1-v[2])*(1-v[3]));
    double h=v[0]/60;
    h-=6*nrFloor(h/6);
    double chroma=(space==2?(1-nrAbs(2*v[2]-1))*v[1]:v[2]*v[1]);
    double x=chroma*(1-nrAbs(h-2*nrFloor(h/2)-1)),off=v[2]-(space==2?chroma/2:chroma);
    double r=0,g=0,b=0;
    switch((int)h) {
        case 0:r=chroma;
        g=x;
        break;
        case 1:r=x;
        g=chroma;
        break;
        case 2:g=chroma;
        b=x;
        break;
        case 3:g=x;
        b=chroma;
        break;
        case 4:r=x;
        b=chroma;
        break;
        default:r=chroma;
        b=x;
    }
    return nrRgb(r+off,g+off,b+off);
}
uint32_t nrPaint(const State*s,int id,uint64_t time,double index,double*alpha) {
    if(id<0||id>=NR_MATERIALS||!s->materials[id].used)id=0;
    const Material*m=&s->materials[id];
    double n=m->scope?index:0,v[4];
    for(int k=0; k<4; k++)v[k]=nrTrack(&m->channel[k],time,n);
    *alpha=nrClamp(nrTrack(&m->alpha,time,n),0,1);
    if(m->gradientCount>0) {
        double phase=nrTrack(&m->index,time,n);
        phase+=n*m->spacing;
        phase-=nrFloor(phase);
        phase*=m->gradientCount;
        int a=(int)phase,b=(a+1)%m->gradientCount;
        double t=phase-a;
        for(int k=0; k<4; k++) {
            double d=m->stops[b][k]-m->stops[a][k];
            if(k==2&&m->space==0) {
                while(d>180)d-=360;
                while(d< -180)d+=360;
            }
            v[k]=m->stops[a][k]+d*t;
        }
    }
    if(m->space==7) {
        if(!m->colorCount)return 0;
        double f=v[0];
        f-=m->colorCount*nrFloor(f/m->colorCount);
        return m->colors[(int)f];
    }
    if(m->space==0)v[2]+=m->hueStep*n;
    else if(m->space==2||m->space==3)v[0]+=m->hueStep*n;
    return colorSpace(m->space,v);
}
/* Immutable tables avoid initialization and retain the snapshot IEEE polynomial. */
#include "crc_tables.h"
uint32_t nrCrc(const void*data,uint32_t length) {
    uint32_t crc=~0u;
    const uint8_t*b=data;
    while(length>=8) {
        /* Explicit byte loads support every alignment and host byte order. */
        crc^=(uint32_t)b[0]|((uint32_t)b[1]<<8)|
             ((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);
        crc=nrCrcTables[7][crc&255]^nrCrcTables[6][(crc>>8)&255]^
            nrCrcTables[5][(crc>>16)&255]^nrCrcTables[4][crc>>24]^
            nrCrcTables[3][b[4]]^nrCrcTables[2][b[5]]^
            nrCrcTables[1][b[6]]^nrCrcTables[0][b[7]];
        b+=8;length-=8;
    }
    while(length--)crc=(crc>>8)^nrCrcTables[0][(crc^*b++)&255];
    return ~crc;
}

/* Deterministic bounded positive power, avoiding platform libm. Used only with
 * validated nonnegative bases and bounded exponents. ln reduction and exp Taylor
 * coefficients use fixed iteration counts, so native and WASM execute the same. */
double nrPowPositive(double x,double power) {
    if(x<=0)return power==0?1:0;
    if(power==0||x==1)return 1;
    int e=0;while(x<.75){x*=2;e--;}while(x>1.5){x*=.5;e++;}
    double z=(x-1)/(x+1),z2=z*z,term=z,sum=0;
    for(int i=1;i<=39;i+=2){sum+=term/i;term*=z2;}
    double y=(2*sum+e*.69314718055994530942)*power;
    if(y< -700)return 0;if(y>700)y=700;
    int n=(int)nrFloor(y/.69314718055994530942+.5);
    double r=y-n*.69314718055994530942,value=1,t=1;
    for(int i=1;i<=18;i++){t*=r/i;value+=t;}
    while(n>0){value*=2;n--;}while(n<0){value*=.5;n++;}return value;
}
uint32_t nrHueShift(uint32_t color,double degrees) {
    if(degrees==0)return color;
    double R=SRGB_LINEAR[(color>>16)&255],G=SRGB_LINEAR[(color>>8)&255],B=SRGB_LINEAR[color&255];
    double l=nrPowPositive(.4122214708*R+.5363325363*G+.0514459929*B,1.0/3);
    double m=nrPowPositive(.2119034982*R+.6806995451*G+.1073969566*B,1.0/3);
    double s=nrPowPositive(.0883024619*R+.2817188376*G+.6299787005*B,1.0/3);
    double L=.2104542553*l+.793617785*m-.0040720468*s;
    double a=1.9779984951*l-2.428592205*m+.4505937099*s,b=.0259040371*l+.7827717662*m-.808675766*s;
    return nrLabColor(nrClamp(L,0,1),a*nrCos(degrees)-b*nrSin(degrees),a*nrSin(degrees)+b*nrCos(degrees));
}
