#include "internal.h"

/* Diagonal inertias and conductances are expressed in one explicit shared
 * principal frame. This is exact linear exchange, not a rotating tensor solver. */
int nrAngularDragExchange(const double*bodyInertia,const double*waterInertia,
                         const double*conductance,double seconds,
                         const double*bodyOmega,const double*waterOmega,
                         double*out,uint32_t capacity){
 if(!bodyInertia||!waterInertia||!conductance||!bodyOmega||!waterOmega||!out||capacity<10||
    ((uintptr_t)bodyInertia%8)||((uintptr_t)waterInertia%8)||((uintptr_t)conductance%8)||
    ((uintptr_t)bodyOmega%8)||((uintptr_t)waterOmega%8)||((uintptr_t)out%8))return -1;
 double row[10]={0};
 for(int axis=0;axis<3;axis++){
  double a[3]={bodyOmega[axis],0,0},b[3]={waterOmega[axis],0,0},exchange[10];
  if(nrFluidDragExchange(bodyInertia[axis],waterInertia[axis],conductance[axis],seconds,a,b,exchange,10)!=1)return -1;
  row[axis]=exchange[0];row[axis+3]=exchange[3];row[axis+6]=exchange[6];row[9]+=exchange[9];
 }
 if(!(row[9]>=0&&row[9]<=1e30))return -1;
 memcpy(out,row,sizeof(row));return 1;
}
