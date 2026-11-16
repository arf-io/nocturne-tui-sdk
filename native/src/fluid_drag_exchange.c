#include "internal.h"
/* Stable 1-exp(-x), including tiny impulses that subtraction would erase. */
double nrDragResponseFraction(double x){
 if(x>745)return 1;int squares=0;while(x>.125){x*=.5;squares++;}
 double result=x,term=x;for(int k=2;k<=20;k++){term*= -x/k;result+=term;}
 for(int k=0;k<squares;k++)result*=2-result;return result;
}
int nrFluidDragExchange(double bodyMass,double waterMass,double conductance,double seconds,const double*bodyVelocity,const double*waterVelocity,double*out,uint32_t capacity){
 if(!bodyVelocity||!waterVelocity||!out||((uintptr_t)bodyVelocity%8)||((uintptr_t)waterVelocity%8)||((uintptr_t)out%8)||capacity<10||
    !(bodyMass>=.001&&bodyMass<=1e12&&waterMass>=.001&&waterMass<=1e12&&conductance>=0&&conductance<=1e12&&seconds>=0&&seconds<=86400))return -1;
 Vec3 a=nrV(bodyVelocity[0],bodyVelocity[1],bodyVelocity[2]),b=nrV(waterVelocity[0],waterVelocity[1],waterVelocity[2]);
 if(!(a.x>=-1000000&&a.x<=1000000&&a.y>=-1000000&&a.y<=1000000&&a.z>=-1000000&&a.z<=1000000&&b.x>=-1000000&&b.x<=1000000&&b.y>=-1000000&&b.y<=1000000&&b.z>=-1000000&&b.z<=1000000))return -1;
 double reduced=bodyMass*waterMass/(bodyMass+waterMass),f=nrDragResponseFraction(conductance*seconds*(1/bodyMass+1/waterMass));Vec3 relative=nrSub(a,b),impulse=nrScale(relative,reduced*f);
 Vec3 nextA=nrSub(a,nrScale(impulse,1/bodyMass)),nextB=nrAdd(b,nrScale(impulse,1/waterMass));
 double lost=.5*reduced*nrDot(relative,relative)*f*(2-f);
 double row[10]={nextA.x,nextA.y,nextA.z,nextB.x,nextB.y,nextB.z,impulse.x,impulse.y,impulse.z,lost};
 for(int k=0;k<10;k++)if(!(row[k]>=-1e30&&row[k]<=1e30))return -1;
 memcpy(out,row,sizeof(row));return 1;
}
