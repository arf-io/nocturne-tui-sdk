#include "internal.h"
static int reject(NrContext*c){const char*message="Invalid or unavailable angular fluid configuration";memcpy(c->error,message,strlen(message)+1);return -1;}
static int parseAngular(const Json*j,SurfaceFluidAngular*candidate,int*slot,SurfaceFluidPose*pose){
 double id,inertia;
 if(!nrAllowed(j,0,"op surfaceId inertia omega pivot orientation")||!nrNumber(j,nrField(j,0,"surfaceId"),&id)||id<1||id>NR_SURFACES||id!=(uint32_t)id||!nrNumber(j,nrField(j,0,"inertia"),&inertia))return 0;
 Vec3 omega=nrV(0,0,0);int token=nrField(j,0,"omega");
 if(token>=0){if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count!=3)return 0;double values[3];token++;for(int axis=0;axis<3;axis++){if(!nrNumber(j,token,&values[axis]))return 0;token=j->tokens[token].next;}omega=nrV(values[0],values[1],values[2]);}
 memset(pose,0,sizeof(*pose));pose->used=1;pose->orientation[3]=1;
 token=nrField(j,0,"pivot");if(token>=0){
  if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count!=3)return 0;
  double values[3];token++;for(int axis=0;axis<3;axis++){if(!nrNumber(j,token,&values[axis])||!(values[axis]>=-16000&&values[axis]<=16000))return 0;token=j->tokens[token].next;}pose->pivot=nrV(values[0],values[1],values[2]);
 }
 token=nrField(j,0,"orientation");if(token>=0){
  if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count!=4)return 0;
  token++;for(int axis=0;axis<4;axis++){if(!nrNumber(j,token,&pose->orientation[axis]))return 0;token=j->tokens[token].next;}
 }
 if(!nrSurfacePoseAdvance(pose->orientation,nrV(0,0,0),0,pose->orientation)||!nrAngularFluidRecordInit(candidate,inertia,omega))return 0;*slot=(int)id-1;return 1;
}
int nrSurfaceFluidAngularShape(const Json*j){SurfaceFluidAngular candidate;SurfaceFluidPose pose;int slot;return nrEqual(j,nrField(j,0,"op"),"surface-fluid-angular")&&parseAngular(j,&candidate,&slot,&pose);}
int nrSurfaceFluidAngularCommand(NrContext*c,State*s,const Json*j){
 SurfaceFluidAngular candidate;SurfaceFluidPose pose;int slot;if(!parseAngular(j,&candidate,&slot,&pose))return reject(c);
 if(s->schema<NR_STATE_SCHEMA_SURFACE_POSE&&(nrField(j,0,"pivot")>=0||nrField(j,0,"orientation")>=0))return reject(c);
 if(s->schema<NR_STATE_SCHEMA_ANGULAR_FLUID||s->surfaceFluids[slot].used!=1||s->angularFluids[slot].used)return reject(c);
 s->angularFluids[slot]=candidate;
 if(s->schema>=NR_STATE_SCHEMA_SURFACE_POSE)s->surfacePoses[slot]=pose;
 return nrBuildGeometry(s,&s->geometry.index)?0:reject(c);
}
int nrSurfaceFluidAngular(const NrContext*c,uint32_t id,double*out,uint32_t capacity){
 if(!c||c->state.magic!=NR_MAGIC||id<1||id>NR_SURFACES||!out||capacity<12||((uintptr_t)out%8)||!nrExternalOutput(c,out,12*sizeof(double)))return -1;
 const SurfaceFluidAngular*f=&c->state.angularFluids[id-1];if(!f->used)return 0;
 double row[12]={f->inertia,f->omega.x,f->omega.y,f->omega.z,f->initialMomentum.x,f->initialMomentum.y,f->initialMomentum.z,f->bodyImpulse.x,f->bodyImpulse.y,f->bodyImpulse.z,f->dissipatedEnergy,f->initialEnergy};memcpy(out,row,sizeof(row));return 1;
}
