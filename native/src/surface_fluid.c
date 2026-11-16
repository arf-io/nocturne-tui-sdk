#include "internal.h"
static int reject(NrContext*c,const char*text){size_t n=strlen(text);if(n>255)n=255;memcpy(c->error,text,n);c->error[n]=0;return -1;}
static int bounded(Vec3 v,double b){return v.x>=-b&&v.x<=b&&v.y>=-b&&v.y<=b&&v.z>=-b&&v.z<=b;}
int nrValidSurfaceFluids(const State*s){
 for(int i=0;i<NR_SURFACES;i++){
  const SurfaceFluidPose*pose=&s->surfacePoses[i];
  if(pose->used){double check[4];if(pose->used!=1||pose->padding||s->schema<NR_STATE_SCHEMA_SURFACE_POSE||!s->angularFluids[i].used||!bounded(pose->pivot,32760)||!nrSurfacePoseAdvance(pose->orientation,nrV(0,0,0),0,check))return 0;}
  else{const unsigned char*p=(const unsigned char*)pose;for(size_t k=0;k<sizeof(*pose);k++)if(p[k])return 0;if(s->schema>=NR_STATE_SCHEMA_SURFACE_POSE&&s->angularFluids[i].used)return 0;}
  const SurfaceFluidAngular*angular=&s->angularFluids[i];
  const SurfaceFluidAngularHistory*angularHistory=&s->angularHistory[i];
  if(!nrAngularFluidHistoryValid(angularHistory)||(angularHistory->exports&&s->schema<NR_STATE_SCHEMA_ANGULAR_HISTORY)||(angular->used&&s->surfaceFluids[i].used==3&&!angularHistory->exports))return 0;
  if(!nrAngularFluidRecordValid(angular)||(angular->used&&(s->schema<NR_STATE_SCHEMA_ANGULAR_FLUID||!s->surfaceFluids[i].used)))return 0;
  const SurfaceFluidHistory*h=&s->fluidHistory[i];
  if(!h->exports){const unsigned char*p=(const unsigned char*)h;for(size_t k=0;k<sizeof(*h);k++)if(p[k])return 0;}
  else{
   if(s->schema<NR_STATE_SCHEMA_FLUID_HISTORY||h->exports>9007199254740991ull||!(h->mass>0&&h->mass<=1e30&&h->energy>=0&&h->energy<=1e30&&h->initialEnergy>=0&&h->initialEnergy<=1e30&&h->dissipatedEnergy>=0&&h->dissipatedEnergy<=1e30)||!bounded(h->momentum,1e30)||!bounded(h->initialMomentum,1e30)||!bounded(h->bodyImpulse,1e30))return 0;
   Vec3 difference=nrSub(h->momentum,nrAdd(h->initialMomentum,h->bodyImpulse));double tolerance=1e-8*(1+nrSqrt(nrDot(h->initialMomentum,h->initialMomentum))+nrSqrt(nrDot(h->bodyImpulse,h->bodyImpulse)));if(nrSqrt(nrDot(difference,difference))>tolerance)return 0;
  }
  const SurfaceFluid*f=&s->surfaceFluids[i];if(!f->used){const unsigned char*p=(const unsigned char*)f;for(size_t k=0;k<sizeof(*f);k++)if(p[k])return 0;continue;}
  if(s->schema<NR_STATE_SCHEMA_SURFACE_FLUID||(f->used!=1&&f->used!=2&&f->used!=3)||f->padding||(f->used==3&&(s->schema<NR_STATE_SCHEMA_FLUID_HISTORY||!h->exports))||!s->geometry.surfaces[i].used||!(f->mass>=.001&&f->mass<=1e12)||!bounded(f->velocity,32760)||!bounded(f->offset,32760)||!bounded(f->initialMomentum,1e30)||!bounded(f->bodyImpulse,1e30)||!(f->dissipatedEnergy>=0&&f->dissipatedEnergy<=1e30&&f->initialEnergy>=0&&f->initialEnergy<=1e30))return 0;
  Vec3 difference=nrSub(nrScale(f->velocity,f->mass),nrAdd(f->initialMomentum,f->bodyImpulse));double tolerance=1e-8*(1+nrSqrt(nrDot(f->initialMomentum,f->initialMomentum))+nrSqrt(nrDot(f->bodyImpulse,f->bodyImpulse)));if(nrSqrt(nrDot(difference,difference))>tolerance)return 0;
 }
 return 1;
}
static int parseFluid(const Json*j,SurfaceFluid*f,int*slot){
 double id,mass;if(!nrAllowed(j,0,"op surfaceId mass velocity")||!nrNumber(j,nrField(j,0,"surfaceId"),&id)||id<1||id>NR_SURFACES||id!=(uint32_t)id||!nrNumber(j,nrField(j,0,"mass"),&mass)||!(mass>=.001&&mass<=1e12))return 0;
 *slot=(int)id-1;memset(f,0,sizeof(*f));f->used=1;f->mass=mass;
 int t=nrField(j,0,"velocity");if(t>=0){if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=3)return 0;double v[3];t++;for(int k=0;k<3;k++){if(!nrNumber(j,t,&v[k]))return 0;t=j->tokens[t].next;}f->velocity=nrV(v[0],v[1],v[2]);}
 if(!bounded(f->velocity,16000))return 0;f->initialMomentum=nrScale(f->velocity,mass);f->initialEnergy=.5*mass*nrDot(f->velocity,f->velocity);return 1;
}
int nrSurfaceFluidShape(const Json*j){
 int op=nrField(j,0,"op");
 if(nrEqual(j,op,"surface-fluid")){SurfaceFluid f;int slot;return parseFluid(j,&f,&slot);}
 if(nrEqual(j,op,"stop-surface-fluid")||nrEqual(j,op,"export-surface-fluid")){
  double id;return nrAllowed(j,0,"op surfaceId")&&nrNumber(j,nrField(j,0,"surfaceId"),&id)&&id>=1&&id<=NR_SURFACES&&id==(uint32_t)id;
 }
 return 0;
}
int nrSurfaceFluidCommand(NrContext*c,State*s,const Json*j){
 if(nrEqual(j,nrField(j,0,"op"),"stop-surface-fluid")||nrEqual(j,nrField(j,0,"op"),"export-surface-fluid")){
  double id;if(!nrAllowed(j,0,"op surfaceId")||!nrNumber(j,nrField(j,0,"surfaceId"),&id)||id<1||id>NR_SURFACES||id!=(uint32_t)id)return reject(c,"Invalid finite water stop");
  SurfaceFluid*f=&s->surfaceFluids[(int)id-1];if(!f->used)return reject(c,"Finite water is unconfigured");if(f->used==3)return 0;
  if(nrEqual(j,nrField(j,0,"op"),"export-surface-fluid")){
   SurfaceFluidAngular*angular=&s->angularFluids[(int)id-1];
   if(angular->used&&!nrAngularFluidArchive(&s->angularHistory[(int)id-1],angular))return reject(c,"Angular export ledger range");
   SurfaceFluidHistory*h=&s->fluidHistory[(int)id-1];if(h->exports>=9007199254740991ull)return reject(c,"Fluid export identity range");
   h->mass+=f->mass;h->energy+=.5*f->mass*nrDot(f->velocity,f->velocity);h->momentum=nrAdd(h->momentum,nrScale(f->velocity,f->mass));h->initialMomentum=nrAdd(h->initialMomentum,f->initialMomentum);h->bodyImpulse=nrAdd(h->bodyImpulse,f->bodyImpulse);h->initialEnergy+=f->initialEnergy;h->dissipatedEnergy+=f->dissipatedEnergy;h->exports++;f->used=3;
   return nrValidSurfaceFluids(s)?0:reject(c,"Fluid export ledger range");
  }
  f->used=2;return 0;
 }
 SurfaceFluid f;int slot;if(!parseFluid(j,&f,&slot))return reject(c,"Invalid finite water settings");
 if(!s->geometry.surfaces[slot].used||(s->surfaceFluids[slot].used&&s->surfaceFluids[slot].used!=3))return reject(c,"Finite water requires an unconfigured named surface");
 f.offset=s->surfaceFluids[slot].offset;s->surfaceFluids[slot]=f;memset(&s->angularFluids[slot],0,sizeof(s->angularFluids[slot]));memset(&s->surfacePoses[slot],0,sizeof(s->surfacePoses[slot]));return nrBuildGeometry(s,&s->geometry.index)?0:reject(c,"Finite water geometry range");
}
int nrSurfaceFluid(const NrContext*c,uint32_t id,double*out,uint32_t capacity){
 if(!c||c->state.magic!=NR_MAGIC||id<1||id>NR_SURFACES||!out||capacity<15||((uintptr_t)out%8)||!nrExternalOutput(c,out,15*sizeof(double)))return -1;
 const SurfaceFluid*f=&c->state.surfaceFluids[id-1];if(!f->used)return 0;
 double row[15]={f->mass,f->velocity.x,f->velocity.y,f->velocity.z,f->offset.x,f->offset.y,f->offset.z,f->initialMomentum.x,f->initialMomentum.y,f->initialMomentum.z,f->bodyImpulse.x,f->bodyImpulse.y,f->bodyImpulse.z,f->dissipatedEnergy,f->initialEnergy};memcpy(out,row,sizeof(row));return 1;
}
int nrSurfaceFluidsTick(State*s){
 int active=0;for(int i=0;i<NR_SURFACES;i++)if(s->surfaceFluids[i].used==1){SurfaceFluid*f=&s->surfaceFluids[i];f->offset=nrAdd(f->offset,nrScale(f->velocity,1.0/120));if(!bounded(f->offset,32760))return 0;
  SurfaceFluidPose*pose=&s->surfacePoses[i];if(pose->used&&!nrSurfacePoseAdvance(pose->orientation,s->angularFluids[i].omega,1.0/120,pose->orientation))return 0;
  active=1;}
 return nrValidSurfaceFluids(s)&&(!active||nrBuildGeometry(s,&s->geometry.index));
}
int nrSurfaceFluidExchange(State*s,FloatBody*b,Vec3 velocity,double seconds){
 SurfaceFluid*f=&s->surfaceFluids[b->surfaceId-1];if(f->used!=1)return 0;
 SurfaceFluidAngular*angular=&s->angularFluids[b->surfaceId-1];const SurfaceFluidPose*pose=&s->surfacePoses[b->surfaceId-1];
 if(angular->used&&pose->used){
  Vec3 radius=nrSub(b->position,nrAdd(pose->pivot,f->offset));double row[13];
  if(!nrFluidPointDragExchange(b->mass,f->mass,angular->inertia,b->mass*b->drag*b->immersion,seconds,velocity,f->velocity,angular->omega,radius,row))return -1;
  Vec3 impulse=nrV(row[9],row[10],row[11]);b->velocity=nrV(row[0],row[1],row[2]);f->velocity=nrV(row[3],row[4],row[5]);angular->omega=nrV(row[6],row[7],row[8]);
  f->bodyImpulse=nrAdd(f->bodyImpulse,impulse);angular->bodyImpulse=nrAdd(angular->bodyImpulse,nrCross(radius,impulse));
  /* Record point-exchange dissipation once in the translational ledger; the
   * separately retained rotational kinetic energy is already in its ledger. */
  f->dissipatedEnergy+=row[12];return nrValidSurfaceFluids(s)?1:-1;
 }
 double a[3]={velocity.x,velocity.y,velocity.z},water[3]={f->velocity.x,f->velocity.y,f->velocity.z},out[10];
 if(nrFluidDragExchange(b->mass,f->mass,b->mass*b->drag*b->immersion,seconds,a,water,out,10)!=1)return -1;
 b->velocity=nrV(out[0],out[1],out[2]);f->velocity=nrV(out[3],out[4],out[5]);f->bodyImpulse=nrAdd(f->bodyImpulse,nrV(out[6],out[7],out[8]));f->dissipatedEnergy+=out[9];return nrValidSurfaceFluids(s)?1:-1;
}
