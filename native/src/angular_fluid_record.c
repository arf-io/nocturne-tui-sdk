#include "internal.h"
static int bounded(Vec3 v,double limit){return v.x>=-limit&&v.x<=limit&&v.y>=-limit&&v.y<=limit&&v.z>=-limit&&v.z<=limit;}
int nrAngularFluidRecordValid(const SurfaceFluidAngular*f){
 if(!f||((uintptr_t)f%_Alignof(SurfaceFluidAngular)))return 0;
 if(!f->used){const unsigned char*p=(const unsigned char*)f;for(size_t i=0;i<sizeof(*f);i++)if(p[i])return 0;return 1;}
 if(f->used!=1||f->padding||!(f->inertia>=.001&&f->inertia<=1e12)||!bounded(f->omega,32760)||!bounded(f->initialMomentum,1e30)||!bounded(f->bodyImpulse,1e30)||!(f->dissipatedEnergy>=0&&f->dissipatedEnergy<=1e30&&f->initialEnergy>=0&&f->initialEnergy<=1e30))return 0;
 Vec3 expected=nrAdd(f->initialMomentum,f->bodyImpulse),difference=nrSub(nrScale(f->omega,f->inertia),expected);
 double tolerance=1e-8*(1+nrSqrt(nrDot(f->initialMomentum,f->initialMomentum))+nrSqrt(nrDot(f->bodyImpulse,f->bodyImpulse)));
 return nrSqrt(nrDot(difference,difference))<=tolerance;
}
int nrAngularFluidRecordInit(SurfaceFluidAngular*out,double inertia,Vec3 omega){
 if(!out||((uintptr_t)out%_Alignof(SurfaceFluidAngular))||!bounded(omega,16000))return 0;
 SurfaceFluidAngular candidate;memset(&candidate,0,sizeof(candidate));candidate.used=1;candidate.inertia=inertia;candidate.omega=omega;
 candidate.initialMomentum=nrScale(omega,inertia);candidate.initialEnergy=.5*inertia*nrDot(omega,omega);
 if(!nrAngularFluidRecordValid(&candidate))return 0;
 memcpy(out,&candidate,sizeof(candidate));return 1;
}
static Vec3 rotate(Vec3 v,Vec3 q,double scalar,int inverse){
 if(inverse)q=nrScale(q,-1);Vec3 t=nrScale(nrCross(q,v),2);
 return nrAdd(v,nrAdd(nrScale(t,scalar),nrCross(q,t)));
}
int nrAngularFluidRecordExchange(SurfaceFluidAngular*f,Vec3 bodyInertia,Vec3 bodyOmega,
                                Vec3 conductance,double seconds,const double*orientation,Vec3*outBodyOmega){
 if(!nrAngularFluidRecordValid(f)||!f->used||!orientation||((uintptr_t)orientation%8)||!outBodyOmega||((uintptr_t)outBodyOmega%_Alignof(Vec3)))return 0;
 uintptr_t record=(uintptr_t)f,output=(uintptr_t)outBodyOmega;
 if(output<record+sizeof(*f)&&record<output+sizeof(*outBodyOmega))return 0;
 double norm=0;for(int axis=0;axis<4;axis++){if(!(orientation[axis]>=-1&&orientation[axis]<=1))return 0;norm+=orientation[axis]*orientation[axis];}
 if(!(norm>=.999999&&norm<=1.000001))return 0;norm=nrSqrt(norm);
 Vec3 q=nrV(orientation[0]/norm,orientation[1]/norm,orientation[2]/norm);double scalar=orientation[3]/norm;
 Vec3 localWater=rotate(f->omega,q,scalar,1);
 double inertia[3]={bodyInertia.x,bodyInertia.y,bodyInertia.z},water[3]={f->inertia,f->inertia,f->inertia};
 double rates[3]={conductance.x,conductance.y,conductance.z},a[3]={bodyOmega.x,bodyOmega.y,bodyOmega.z},b[3]={localWater.x,localWater.y,localWater.z},row[10];
 if(nrAngularDragExchange(inertia,water,rates,seconds,a,b,row,10)!=1)return 0;
 SurfaceFluidAngular candidate=*f;candidate.omega=rotate(nrV(row[3],row[4],row[5]),q,scalar,0);
 candidate.bodyImpulse=nrAdd(candidate.bodyImpulse,rotate(nrV(row[6],row[7],row[8]),q,scalar,0));candidate.dissipatedEnergy+=row[9];
 Vec3 body=nrV(row[0],row[1],row[2]);if(!bounded(body,1000)||!nrAngularFluidRecordValid(&candidate))return 0;
 *f=candidate;*outBodyOmega=body;return 1;
}
