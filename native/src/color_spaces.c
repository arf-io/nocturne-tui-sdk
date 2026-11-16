#include "internal.h"
/* Deterministic interpolation, using the same fixed power/trigonometry kernels
 * as native materials. space: 0 encoded RGB, 1 linear RGB, 2 OKLab, 3 OKLCh. */
static double decode(double c){return c<=.04045?c/12.92:nrPowPositive((c+.055)/1.055,2.4);}
static double encode(double c){c=nrClamp(c,0,1);return c<=.0031308?12.92*c:1.055*nrPowPositive(c,1/2.4)-.055;}
static void lab(const double*c,double*out){
    double r=decode(c[0]),g=decode(c[1]),b=decode(c[2]);
    double l=nrPowPositive(.4122214708*r+.5363325363*g+.0514459929*b,1.0/3);
    double m=nrPowPositive(.2119034982*r+.6806995451*g+.1073969566*b,1.0/3);
    double s=nrPowPositive(.0883024619*r+.2817188376*g+.6299787005*b,1.0/3);
    out[0]=.2104542553*l+.793617785*m-.0040720468*s;
    out[1]=1.9779984951*l-2.428592205*m+.4505937099*s;
    out[2]=.0259040371*l+.7827717662*m-.808675766*s;
}
static double hue(double a,double b){
    if(a==0&&b==0)return 0;
    double lo=0,hi=90,x=nrAbs(a),y=nrAbs(b);
    for(int i=0;i<36;i++){double mid=(lo+hi)*.5;if(nrSin(mid)*x<nrCos(mid)*y)lo=mid;else hi=mid;}
    double angle=(lo+hi)*.5;
    if(a<0)angle=180-angle;if(b<0)angle=360-angle;return angle;
}
static void labRgb(double L,double a,double b,double*out){
    double l=L+.3963377774*a+.2158037573*b,m=L-.1055613458*a-.0638541728*b,s=L-.0894841775*a-1.291485548*b;
    l=l*l*l;m=m*m*m;s=s*s*s;
    out[0]=4.0767416621*l-3.3077115913*m+.2309699292*s;
    out[1]=-1.2684380046*l+2.6097574011*m-.3413193965*s;
    out[2]=-.0041960863*l-.7034186147*m+1.707614701*s;
}
static int gamut(const double*c){return c[0]>=-1e-7&&c[0]<=1+1e-7&&c[1]>=-1e-7&&c[1]<=1+1e-7&&c[2]>=-1e-7&&c[2]<=1+1e-7;}
void nrRotateColorHue(const double*input,double degrees,double*out){
    double v[3];lab(input,v);double a=v[1]*nrCos(degrees)-v[2]*nrSin(degrees),b=v[1]*nrSin(degrees)+v[2]*nrCos(degrees);
    double chroma=nrSqrt(a*a+b*b);if(chroma>.5){a*=.5/chroma;b*=.5/chroma;}
    labRgb(v[0],a,b,out);
    if(!gamut(out)){
        double lo=0,hi=1;
        for(int i=0;i<24;i++){double mid=(lo+hi)*.5,test[3];labRgb(v[0],a*mid,b*mid,test);if(gamut(test))lo=mid;else hi=mid;}
        labRgb(v[0],a*lo,b*lo,out);
    }
    for(int k=0;k<3;k++)out[k]=encode(out[k]);
}
uint32_t nrMixColorSpace(const double*from,const double*to,double t,uint32_t space){
    if(t<=0)return nrRgb(from[0],from[1],from[2]);
    if(t>=1)return nrRgb(to[0],to[1],to[2]);
    double v[3];
    if(space<=1){
        for(int i=0;i<3;i++){double a=space?decode(from[i]):from[i],b=space?decode(to[i]):to[i];v[i]=a+(b-a)*t;if(space)v[i]=encode(v[i]);}
        return nrRgb(v[0],v[1],v[2]);
    }
    double a[3],b[3];lab(from,a);lab(to,b);
    for(int i=0;i<3;i++)v[i]=a[i]+(b[i]-a[i])*t;
    if(space==3){
        double ca=nrSqrt(a[1]*a[1]+a[2]*a[2]),cb=nrSqrt(b[1]*b[1]+b[2]*b[2]);
        double ha=hue(a[1],a[2]),hb=hue(b[1],b[2]);
        if(ca<1e-7)ha=hb;if(cb<1e-7)hb=ha;
        double delta=hb-ha;while(delta>180)delta-=360;while(delta< -180)delta+=360;
        double h=ha+delta*t,c=nrClamp(ca+(cb-ca)*t,0,.5);
        v[1]=c*nrCos(h);v[2]=c*nrSin(h);
    }
    return nrLabColor(nrClamp(v[0],0,1),nrClamp(v[1],-.5,.5),nrClamp(v[2],-.5,.5));
}
uint32_t nrColorWithHue(uint32_t rgb,double angle){
    double channels[3]={((rgb>>16)&255)/255.0,((rgb>>8)&255)/255.0,(rgb&255)/255.0},value[3];lab(channels,value);
    double chroma=nrSqrt(value[1]*value[1]+value[2]*value[2]);
    return nrLabColor(value[0],chroma*nrCos(angle),chroma*nrSin(angle));
}
