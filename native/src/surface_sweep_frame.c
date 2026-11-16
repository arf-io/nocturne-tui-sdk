#include "internal.h"

/* Sample the same retained frame at a collision's actual time. Flow extrusion
 * follows its fixed-step endpoint interpolation, matching the existing flow
 * contact solver. Wave phase remains analytic at the requested time. */
int nrSurfaceTriangleAtTime(const State*s,int index,double seconds,Triangle*out,Vec3*outVelocity){
 if(!s||index<0||index>=s->meshCount||!out||!outVelocity||!(seconds>=0&&seconds<=1000000))return -1;
 int id=s->geometry.triangleSurfaces[index];if(id<1||id>NR_SURFACES)return -1;
 Triangle candidate=s->mesh[index];Vec3 localVelocity[3]={nrV(0,0,0),nrV(0,0,0),nrV(0,0,0)};
 double current=s->timeUs/1000000.0;
 if(s->flowThicknessTriangles[index].role){
  uint64_t begin=s->step?((uint64_t)(s->step-1)*1000000)/120:s->timeUs;
  Triangle a,b;int first=nrFlowThicknessTriangleAt(s,index,begin,&a),last=nrFlowThicknessTriangleAt(s,index,s->timeUs,&b);
  if(first<1||last<1)return -1;
  if(first==2&&last==2)return 0;
  double span=(s->timeUs-begin)/1000000.0,weight=span>0?(seconds-begin/1000000.0)/span:1;
  if(weight< -1e-9||weight>1+1e-9)return -1;weight=nrClamp(weight,0,1);
  Vec3 left[3]={a.a,a.b,a.c},right[3]={b.a,b.b,b.c},*points[3]={&candidate.a,&candidate.b,&candidate.c};
  for(int k=0;k<3;k++){Vec3 movement=nrSub(right[k],left[k]);*points[k]=nrAdd(left[k],nrScale(movement,weight));if(span>0)localVelocity[k]=nrScale(movement,1/span);}
 }
 Vec3*points[3]={&candidate.a,&candidate.b,&candidate.c};double sample[6];
 for(int k=0;k<3;k++)if(s->surfaceWaves[id-1].count){
  if(nrWaveSample(&s->surfaceWaves[id-1].waves[0][0],s->surfaceWaves[id-1].count,points[k]->x,points[k]->z,seconds,sample,6)!=1)return -1;
  points[k]->y+=sample[0];localVelocity[k].y+=sample[4];
 }
 const SurfaceFluid*f=&s->surfaceFluids[id-1];const SurfaceFluidPose*pose=&s->surfacePoses[id-1];
 Vec3 translation=f->used==1?f->velocity:nrV(0,0,0),omega=f->used==1?s->angularFluids[id-1].omega:nrV(0,0,0);
 Vec3 offset=nrAdd(f->offset,nrScale(translation,seconds-current)),velocities[3];double q[4];
 if(pose->used&&!nrSurfacePoseAdvance(pose->orientation,omega,seconds-current,q))return -1;
 for(int k=0;k<3;k++){
  if(pose->used){
   if(!nrSurfacePoseMotion(q,pose->pivot,offset,omega,translation,*points[k],sample))return -1;
   *points[k]=nrV(sample[0],sample[1],sample[2]);Vec3 rigid=nrV(sample[3],sample[4],sample[5]);
   Vec3 vector=nrV(q[0],q[1],q[2]),t=nrScale(nrCross(vector,localVelocity[k]),2);
   velocities[k]=nrAdd(rigid,nrAdd(localVelocity[k],nrAdd(nrScale(t,q[3]),nrCross(vector,t))));
  }else{*points[k]=nrAdd(*points[k],offset);velocities[k]=nrAdd(translation,localVelocity[k]);}
 }
 *out=candidate;memcpy(outVelocity,velocities,sizeof(velocities));return 1;
}
