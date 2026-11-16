#include "internal.h"
static int bounded(Vec3 v){return v.x>=-1e30&&v.x<=1e30&&v.y>=-1e30&&v.y<=1e30&&v.z>=-1e30&&v.z<=1e30;}
int nrAngularFluidHistoryValid(const SurfaceFluidAngularHistory*h){
 if(!h||((uintptr_t)h%_Alignof(SurfaceFluidAngularHistory)))return 0;
 if(!h->exports){const unsigned char*p=(const unsigned char*)h;for(size_t i=0;i<sizeof(*h);i++)if(p[i])return 0;return 1;}
 if(h->exports>9007199254740991ull||!(h->inertia>0&&h->inertia<=1e30&&h->energy>=0&&h->energy<=1e30&&h->initialEnergy>=0&&h->initialEnergy<=1e30&&h->dissipatedEnergy>=0&&h->dissipatedEnergy<=1e30)||!bounded(h->momentum)||!bounded(h->initialMomentum)||!bounded(h->bodyImpulse))return 0;
 Vec3 difference=nrSub(h->momentum,nrAdd(h->initialMomentum,h->bodyImpulse));double tolerance=1e-8*(1+nrSqrt(nrDot(h->initialMomentum,h->initialMomentum))+nrSqrt(nrDot(h->bodyImpulse,h->bodyImpulse)));
 return nrSqrt(nrDot(difference,difference))<=tolerance;
}
int nrAngularFluidArchive(SurfaceFluidAngularHistory*h,const SurfaceFluidAngular*f){
 if(!nrAngularFluidHistoryValid(h)||!nrAngularFluidRecordValid(f)||!f->used||h->exports>=9007199254740991ull)return 0;
 SurfaceFluidAngularHistory candidate=*h;
 candidate.inertia+=f->inertia;candidate.energy+=.5*f->inertia*nrDot(f->omega,f->omega);
 candidate.momentum=nrAdd(candidate.momentum,nrScale(f->omega,f->inertia));candidate.initialMomentum=nrAdd(candidate.initialMomentum,f->initialMomentum);
 candidate.bodyImpulse=nrAdd(candidate.bodyImpulse,f->bodyImpulse);candidate.initialEnergy+=f->initialEnergy;candidate.dissipatedEnergy+=f->dissipatedEnergy;candidate.exports++;
 if(!nrAngularFluidHistoryValid(&candidate))return 0;*h=candidate;return 1;
}
