/* Portable OKLCh conversion, Q20 arithmetic. No floating-point runtime.
 * RGB output is gamut mapped by 14-step chroma reduction at constant L/h.
 * This is NOT the CSS local-MINDE gamut mapper. Precision contract in docs.
 */
#include "nocturne_studio.h"
#include "ok_tables.inc"
#define OK_Q 1048576LL
static int64_t okCube(int64_t x){return (x*x/OK_Q)*x/OK_Q;}
static int64_t okRoot(int64_t x){int64_t lo=0,hi=OK_Q;while(lo<hi){int64_t m=(lo+hi+1)/2;if(okCube(m)<=x)lo=m;else hi=m-1;}return lo;}
static void okLinear(int32_t l,int32_t c,int32_t h,int64_t out[3]){
 int64_t L=(int64_t)l*OK_Q/1000,C=(int64_t)c*OK_Q/10000;
 int32_t phase=(int32_t)((int64_t)modI(h,360000)*1024/360000);
 int64_t a=C*sinI(phase+256)/1000,b=C*sinI(phase)/1000;
 int64_t ll=okCube(L+(396338*a+215804*b)/1000000),m=okCube(L-(105561*a+63854*b)/1000000),s=okCube(L-(89484*a+1291486*b)/1000000);
 out[0]=(4076742*ll-3307712*m+230970*s)/1000000;
 out[1]=(-1268438*ll+2609757*m-341319*s)/1000000;
 out[2]=(-4196*ll-703419*m+1707615*s)/1000000;
}
static int okInGamut(const int64_t rgb[3]){return rgb[0]>=0&&rgb[0]<=OK_Q&&rgb[1]>=0&&rgb[1]<=OK_Q&&rgb[2]>=0&&rgb[2]<=OK_Q;}
static int okGamma(int64_t x){int lo=0,hi=255;while(lo<hi){int mid=(lo+hi)/2;if(x>OK_BOUNDARY[mid])lo=mid+1;else hi=mid;}return lo;}
int32_t nsOklchColor(int32_t lightness,int32_t chroma,int32_t hueMilliDegrees){
 if(lightness<0||lightness>1000||chroma<0||chroma>4000)return -1;
 if(!lightness)return 0;
 if(lightness==1000)return 0xffffff;
 int64_t rgb[3];okLinear(lightness,chroma,hueMilliDegrees,rgb);
 if(!okInGamut(rgb)){int lo=0,hi=chroma;for(int i=0;i<14&&lo<hi;i++){int mid=(lo+hi+1)/2;okLinear(lightness,mid,hueMilliDegrees,rgb);if(okInGamut(rgb))lo=mid;else hi=mid-1;}okLinear(lightness,lo,hueMilliDegrees,rgb);}
 return (int32_t)rgbI(okGamma(rgb[0]),okGamma(rgb[1]),okGamma(rgb[2]));
}
int32_t nsOklchLightness(uint32_t color){
 if(color>0xffffff)return -1;
 int64_t r=OK_LINEAR[redI(color)],g=OK_LINEAR[greenI(color)],b=OK_LINEAR[blueI(color)];
 int64_t l=okRoot((412221*r+536333*g+51446*b)/1000000),m=okRoot((211903*r+680700*g+107397*b)/1000000),s=okRoot((88302*r+281719*g+629979*b)/1000000);
 return (int32_t)(((210454*l+793618*m-4072*s)/1000000)*1000/OK_Q);
}
#undef OK_Q
