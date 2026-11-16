#include "internal.h"

/* Shared rigid reservoir frame. Quaternion components are xyzw, omega is
 * world-frame radians/second, and authored points rotate about an explicit
 * pivot before translation. No state, clock or geometry is mutated here. */
static int finiteVector(Vec3 v,double bound){
 return v.x>=-bound&&v.x<=bound&&v.y>=-bound&&v.y<=bound&&v.z>=-bound&&v.z<=bound;
}
static int orientation(const double*in,double*q){
 if(!in||((uintptr_t)in%8))return 0;
 double norm=0;for(int i=0;i<4;i++){if(!(in[i]>=-1&&in[i]<=1))return 0;q[i]=in[i];norm+=q[i]*q[i];}
 if(!(norm>=.999999&&norm<=1.000001))return 0;
 norm=nrSqrt(norm);for(int i=0;i<4;i++)q[i]/=norm;return 1;
}
static void rotationTrig(double angle,double*sine,double*cosine){
 const double pi=3.14159265358979323846;
 angle-=2*pi*(int64_t)(angle/(2*pi));
 if(angle>pi)angle-=2*pi;if(angle<-pi)angle+=2*pi;
 double sign=1;if(angle>pi/2){angle=pi-angle;sign=-1;}else if(angle<-pi/2){angle=-pi-angle;sign=-1;}
 /* The render lookup table is intentionally unsuitable for accumulated pose
  * integration. These bounded series retain small-angle precision without a
  * platform libm dependency in WASM. */
 double square=angle*angle,st=angle,ct=1,s=st,c=ct;
 for(int k=1;k<=12;k++){st*=-square/((2*k)*(2*k+1));ct*=-square/((2*k-1)*(2*k));s+=st;c+=ct;}
 *sine=s;*cosine=c*sign;
}
int nrSurfacePoseAdvance(const double*in,Vec3 omega,double seconds,double*out){
 double q[4];if(!out||((uintptr_t)out%8)||!orientation(in,q)||!finiteVector(omega,32760)||!(seconds>=-86400&&seconds<=86400))return 0;
 double speed=nrSqrt(nrDot(omega,omega));
 if(speed==0||seconds==0){memcpy(out,q,sizeof(q));return 1;}
 /* Left multiplication gives a world-frame incremental rotation. */
 double sine,cosine;rotationTrig(speed*seconds*.5,&sine,&cosine);
 Vec3 delta=nrScale(omega,sine/speed),vector=nrV(q[0],q[1],q[2]);
 Vec3 result=nrAdd(nrAdd(nrScale(vector,cosine),nrScale(delta,q[3])),nrCross(delta,vector));
 double scalar=cosine*q[3]-nrDot(delta,vector);
 double norm=nrSqrt(nrDot(result,result)+scalar*scalar);
 if(!(norm>0))return 0;
 double row[4]={result.x/norm,result.y/norm,result.z/norm,scalar/norm};memcpy(out,row,sizeof(row));return 1;
}
int nrSurfacePoseInverse(const double*in,Vec3 pivot,Vec3 offset,Vec3 omega,Vec3 velocity,Vec3 point,Vec3 pointVelocity,double*out){
 double q[4];if(!out||((uintptr_t)out%8)||!orientation(in,q)||!finiteVector(pivot,32760)||!finiteVector(offset,32760)||!finiteVector(omega,32760)||!finiteVector(velocity,32760)||!finiteVector(point,131040)||!finiteVector(pointVelocity,1e12))return 0;
 Vec3 radius=nrSub(point,nrAdd(pivot,offset));
 Vec3 relativeVelocity=nrSub(nrSub(pointVelocity,velocity),nrCross(omega,radius));
 Vec3 vector=nrV(-q[0],-q[1],-q[2]);
 Vec3 t=nrScale(nrCross(vector,radius),2),local=nrAdd(pivot,nrAdd(radius,nrAdd(nrScale(t,q[3]),nrCross(vector,t))));
 t=nrScale(nrCross(vector,relativeVelocity),2);
 Vec3 motion=nrAdd(relativeVelocity,nrAdd(nrScale(t,q[3]),nrCross(vector,t)));
 double row[6]={local.x,local.y,local.z,motion.x,motion.y,motion.z};memcpy(out,row,sizeof(row));return 1;
}
int nrSurfacePoseBounds(const double*in,Vec3 pivot,Vec3 offset,Vec3 omega,Vec3 velocity,const double*points,uint32_t count,double seconds,double*out){
 double q[4];
 if(!out||((uintptr_t)out%8)||!points||((uintptr_t)points%8)||!count||count>768||!orientation(in,q)||!finiteVector(pivot,32760)||!finiteVector(offset,32760)||!finiteVector(omega,32760)||!finiteVector(velocity,32760)||!(seconds>=-86400&&seconds<=86400))return 0;
 Vec3 start=nrAdd(pivot,offset),end=nrAdd(start,nrScale(velocity,seconds));
 double low[3]={1e30,1e30,1e30},high[3]={-1e30,-1e30,-1e30},radiusSquared=0;
 int rotating=seconds!=0&&nrDot(omega,omega)>0;
 for(uint32_t i=0;i<count;i++){
  Vec3 point=nrV(points[3*i],points[3*i+1],points[3*i+2]);if(!finiteVector(point,32760))return 0;
  if(rotating){Vec3 delta=nrSub(point,pivot);double squared=nrDot(delta,delta);if(squared>radiusSquared)radiusSquared=squared;}
  else{
   double row[6];if(!nrSurfacePoseMotion(q,pivot,offset,omega,velocity,point,row))return 0;
   double movement[3]={velocity.x*seconds,velocity.y*seconds,velocity.z*seconds};
   for(int axis=0;axis<3;axis++){double a=row[axis],b=a+movement[axis];if(a<low[axis])low[axis]=a;if(b<low[axis])low[axis]=b;if(a>high[axis])high[axis]=a;if(b>high[axis])high[axis]=b;}
  }
 }
 if(rotating){
  /* A point remains inside its pivot-centered sphere for every quaternion.
   * Sweeping that sphere along the translated pivot encloses the entire arc,
   * even if intermediate extrema lie beyond both endpoint triangles. */
  double radius=nrSqrt(radiusSquared),a[3]={start.x,start.y,start.z},b[3]={end.x,end.y,end.z};
  for(int axis=0;axis<3;axis++){low[axis]=(a[axis]<b[axis]?a[axis]:b[axis])-radius;high[axis]=(a[axis]>b[axis]?a[axis]:b[axis])+radius;}
 }
 /* Consume every point before output so late invalid input and point/output
  * aliasing are both atomic. These are broad-phase bounds, not a contact test. */
 double row[6]={low[0],low[1],low[2],high[0],high[1],high[2]};memcpy(out,row,sizeof(row));return 1;
}
int nrSurfacePoseMotion(const double*in,Vec3 pivot,Vec3 offset,Vec3 omega,Vec3 velocity,Vec3 point,double*out){
 double q[4];if(!out||((uintptr_t)out%8)||!orientation(in,q)||!finiteVector(pivot,32760)||!finiteVector(offset,32760)||!finiteVector(omega,32760)||!finiteVector(velocity,32760)||!finiteVector(point,32760))return 0;
 Vec3 relative=nrSub(point,pivot),vector=nrV(q[0],q[1],q[2]),t=nrScale(nrCross(vector,relative),2);
 Vec3 rotated=nrAdd(relative,nrAdd(nrScale(t,q[3]),nrCross(vector,t)));
 Vec3 world=nrAdd(nrAdd(pivot,offset),rotated),motion=nrAdd(velocity,nrCross(omega,rotated));
 double row[6]={world.x,world.y,world.z,motion.x,motion.y,motion.z};memcpy(out,row,sizeof(row));return 1;
}
