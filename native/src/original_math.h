#ifndef NOCTURNE_ORIGINAL_MATH_H
#define NOCTURNE_ORIGINAL_MATH_H
#include "internal.h"
/* Imported fdlibm kernels retain their original license in each source file.
 * Explicit word access is portable across alignment and host byte order. */
static inline int32_t nrOriginalHI(double x){uint64_t bits;memcpy(&bits,&x,8);return (int32_t)(bits>>32);}
static inline uint32_t nrOriginalLO(double x){uint64_t bits;memcpy(&bits,&x,8);return (uint32_t)bits;}
static inline void nrOriginalSetHI(double*x,uint32_t hi){uint64_t bits;memcpy(&bits,x,8);bits=(bits&UINT64_C(0xffffffff))|((uint64_t)hi<<32);memcpy(x,&bits,8);}
static inline void nrOriginalSetLO(double*x,uint32_t lo){uint64_t bits;memcpy(&bits,x,8);bits=(bits&UINT64_C(0xffffffff00000000))|lo;memcpy(x,&bits,8);}
static inline double nrOriginalScalbn(double x,int n){while(n<0){x*=.5;n++;}while(n>0){x*=2;n--;}return x;}
double nrOriginalKernelSin(double,double,int);
double nrOriginalKernelCos(double,double);
double nrOriginalKernelTan(double,double,int);
int nrOriginalRemPi2(double,double*);
int nrOriginalKernelRemPi2(double*,double*,int,int,int,const int*);
double nrOriginalSin(double);
double nrOriginalCos(double);
double nrOriginalTan(double);
double nrOriginalAtan(double);
double nrOriginalAtan2(double,double);
double nrOriginalExp(double);
static inline double nrOriginalHypot(double x,double y,double z){
 double values[3]={nrAbs(x),nrAbs(y),nrAbs(z)},maximum=values[0];if(values[1]>maximum)maximum=values[1];if(values[2]>maximum)maximum=values[2];if(!maximum)return 0;
 double sum=0,compensation=0;for(int i=0;i<3;i++){double n=values[i]/maximum,summand=n*n-compensation,preliminary=sum+summand;compensation=(preliminary-sum)-summand;sum=preliminary;}return __builtin_sqrt(sum)*maximum;
}
#endif
