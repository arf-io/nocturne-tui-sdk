#include "internal.h"

static int finitePoint(Vec3 point){return point.x-point.x==0&&point.y-point.y==0&&point.z-point.z==0;}

static Vec3 segmentClosest(Vec3 point,Vec3 a,Vec3 b,double*fraction){
 Vec3 edge=nrSub(b,a);double length=nrDot(edge,edge);
 *fraction=length>0?nrClamp(nrDot(nrSub(point,a),edge)/length,0,1):0;
 return nrAdd(a,nrScale(edge,*fraction));
}
static double triangleDistance(Vec3 point,const Triangle*t,double*weights){
 Vec3 ab=nrSub(t->b,t->a),ac=nrSub(t->c,t->a),ap=nrSub(point,t->a);
 double aa=nrDot(ab,ab),bb=nrDot(ac,ac),cross=nrDot(ab,ac),det=aa*bb-cross*cross;
 if(det>1e-20){
  double u=(nrDot(ap,ab)*bb-nrDot(ap,ac)*cross)/det,v=(nrDot(ap,ac)*aa-nrDot(ap,ab)*cross)/det;
  if(u>=0&&v>=0&&u+v<=1){weights[0]=1-u-v;weights[1]=u;weights[2]=v;Vec3 offset=nrSub(ap,nrAdd(nrScale(ab,u),nrScale(ac,v)));return nrSqrt(nrDot(offset,offset));}
 }
 Vec3 vertices[3]={t->a,t->b,t->c};double best=1e30;
 for(int edge=0;edge<3;edge++){double fraction;Vec3 closest=segmentClosest(point,vertices[edge],vertices[(edge+1)%3],&fraction),offset=nrSub(point,closest);double distance=nrSqrt(nrDot(offset,offset));
  if(distance<best){best=distance;weights[0]=weights[1]=weights[2]=0;weights[edge]=1-fraction;weights[(edge+1)%3]=fraction;}}
 return best;
}
int nrRotatingSurfaceHit(const State*s,int index,Vec3 from,Vec3 to,double start,double duration,double maximum,GeometryHit*out){
 if(!s||index<0||index>=s->meshCount||!out||((uintptr_t)out%_Alignof(GeometryHit))||!finitePoint(from)||!finitePoint(to)||!(start>=0&&start<=1000000&&duration>0&&duration<=1000000-start&&maximum>=0&&maximum<=1))return -1;
 int id=s->geometry.triangleSurfaces[index];if(id<1||id>NR_SURFACES||!s->surfacePoses[id-1].used)return -1;
 const SurfaceFluid*f=&s->surfaceFluids[id-1];const SurfaceFluidPose*pose=&s->surfacePoses[id-1];
 Vec3 delta=nrSub(to,from),linear=f->used==1?f->velocity:nrV(0,0,0),omega=f->used==1?s->angularFluids[id-1].omega:nrV(0,0,0);
 /* A rigid nonrotating plane admits an exact separation certificate. This
  * prevents near-parallel misses from exhausting distance advancement while
  * leaving coplanar edge contacts to the full triangle-distance search. */
 if(nrDot(omega,omega)==0&&!s->surfaceWaves[id-1].count&&!s->flowThicknessTriangles[index].role){
  Triangle plane;Vec3 velocities[3];if(nrSurfaceTriangleAtTime(s,index,start,&plane,velocities)!=1)return -1;
  Vec3 normal=nrNormal(nrCross(nrSub(plane.b,plane.a),nrSub(plane.c,plane.a)));
  double left=nrDot(normal,nrSub(from,plane.a));
  double right=left+nrDot(normal,nrSub(delta,nrScale(linear,duration)))*maximum;
  if((left>1e-8&&right>1e-8)||(left< -1e-8&&right< -1e-8))return 0;
 }
 double amplitude=0,waveSpeed=0;
 for(uint32_t wave=0;wave<s->surfaceWaves[id-1].count;wave++){const double*w=s->surfaceWaves[id-1].waves[wave];amplitude+=nrAbs(w[0]);waveSpeed+=nrAbs(w[0]*w[3]);}
 Triangle base=s->mesh[index];Vec3 vertices[3]={base.a,base.b,base.c};double radius=0,flowSpeed=0;
 for(int k=0;k<3;k++){Vec3 relative=nrSub(vertices[k],pose->pivot);double length=nrSqrt(nrDot(relative,relative));if(length>radius)radius=length;}
 if(s->flowThicknessTriangles[index].role){
  uint64_t begin=s->step?((uint64_t)(s->step-1)*1000000)/120:s->timeUs;double span=(s->timeUs-begin)/1000000.0;
  if(start<begin/1000000.0-1e-9||start+duration> s->timeUs/1000000.0+1e-9)return -1;
  Triangle a,b;int first=nrFlowThicknessTriangleAt(s,index,begin,&a),last=nrFlowThicknessTriangleAt(s,index,s->timeUs,&b);if(first<1||last<1)return -1;if(first==2&&last==2)return 0;
  Vec3 left[3]={a.a,a.b,a.c},right[3]={b.a,b.b,b.c};
  for(int k=0;k<3;k++){Vec3 movement=nrSub(right[k],left[k]);double speed=span>0?nrSqrt(nrDot(movement,movement))/span:0;if(speed>flowSpeed)flowSpeed=speed;}
  radius+=s->flowThickness[id-1].maxDepth;
 }
 double speed=nrSqrt(nrDot(delta,delta))/duration+nrSqrt(nrDot(linear,linear))+nrSqrt(nrDot(omega,omega))*(radius+amplitude)+waveSpeed+flowSpeed;
 if(!(speed>=0&&speed-speed==0))return -1;
 double fraction=0;
 for(int work=0;work<4096;work++){
  Triangle triangle;Vec3 velocities[3];int sampled=nrSurfaceTriangleAtTime(s,index,start+fraction*duration,&triangle,velocities);
  if(sampled<0)return -1;if(!sampled)return 0;
  Vec3 point=nrAdd(from,nrScale(delta,fraction));double weights[3];double distance=triangleDistance(point,&triangle,weights);
  if(distance<=1e-8){
   Vec3 normal=nrNormal(nrCross(nrSub(triangle.b,triangle.a),nrSub(triangle.c,triangle.a)));
   if(nrDot(normal,normal)<.5)return -1;
   Vec3 velocity=nrV(0,0,0);for(int k=0;k<3;k++)velocity=nrAdd(velocity,nrScale(velocities[k],weights[k]));
   if(nrDot(normal,nrSub(nrScale(delta,1/duration),velocity))>0)normal=nrScale(normal,-1);
   GeometryHit hit;memset(&hit,0,sizeof(hit));hit.surfaceId=id;hit.triangleIndex=index;hit.fraction=fraction;hit.position=point;hit.normal=normal;hit.surfaceVelocity=velocity;*out=hit;return 1;
  }
  if(speed<=0)return 0;
  /* Distance to a triangle is Lipschitz under vertex motion. No endpoint-only
   * miss certificate is used, including edge and interior arc contacts. */
  double safe=distance/(speed*duration);
  if(safe>maximum-fraction)return 0;
  double next=fraction+.8*safe;if(next<=fraction)return -1;fraction=next;
 }
 return -1;
}
