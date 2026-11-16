#include "internal.h"
static int reject(NrContext*c,const char*text){if(!c)return -1;size_t n=strlen(text);if(n>255)n=255;memcpy(c->error,text,n);c->error[n]=0;return -1;}
static int row(const Json*j,int t,double*out,int count){if(t<0||j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=count)return 0;t++;for(int i=0;i<count;i++){if(!nrNumber(j,t,&out[i]))return 0;t=j->tokens[t].next;}return 1;}
static int vectorValid(Vec3 v,double bound){return v.x>=-bound&&v.x<=bound&&v.y>=-bound&&v.y<=bound&&v.z>=-bound&&v.z<=bound;}
static int valid(const FloatHull*h){
 if(h->used!=1||h->padding||h->vertexCount<4||h->vertexCount>128||h->faceCount<4||h->faceCount>256||!vectorValid(h->angularVelocity,1000)||!vectorValid(h->centerOfMass,16000))return 0;
 if(!(h->inertia.x>=.001&&h->inertia.x<=1e12&&h->inertia.y>=.001&&h->inertia.y<=1e12&&h->inertia.z>=.001&&h->inertia.z<=1e12))return 0;
 double norm=0;for(int i=0;i<4;i++){if(!(h->orientation[i]>=-1&&h->orientation[i]<=1))return 0;norm+=h->orientation[i]*h->orientation[i];}if(!(norm>=.999999&&norm<=1.000001))return 0;
 for(uint32_t i=0;i<h->vertexCount;i++)if(!vectorValid(h->vertices[i],16000))return 0;
 for(uint32_t i=h->vertexCount;i<128;i++)if(h->vertices[i].x||h->vertices[i].y||h->vertices[i].z)return 0;
 for(uint32_t i=h->faceCount;i<256;i++)for(int k=0;k<3;k++)if(h->faces[i][k])return 0;
 double out[5];if(nrHullImmersion((const double*)h->vertices,h->vertexCount,&h->faces[0][0],h->faceCount,-1000000,out,5)!=1)return 0;
 return h->volume==out[0];
}
int nrValidFloatHulls(const State*s){
 for(int i=0;i<NR_FLOAT_BODIES;i++){
  const FloatHull*h=&s->floatHulls[i];
  if(!h->used){const unsigned char*bytes=(const unsigned char*)h;for(size_t k=0;k<sizeof(*h);k++)if(bytes[k])return 0;continue;}
  if(s->schema<NR_STATE_SCHEMA_FLOAT_HULLS||!s->floatBodies[i].used||!valid(h))return 0;
 }
 return 1;
}
static int parseHull(NrContext*c,const Json*j,FloatHull*h){
 if(!nrAllowed(j,0,"op id vertices faces inertia centerOfMass orientation angularVelocity"))return reject(c,"Unknown hull field");
 memset(h,0,sizeof(*h));h->used=1;h->orientation[3]=1;int t;
 int vertices=nrField(j,0,"vertices"),faces=nrField(j,0,"faces");
 if(vertices<0||faces<0||j->tokens[vertices].type!=J_ARRAY||j->tokens[faces].type!=J_ARRAY||j->tokens[vertices].count<4||j->tokens[vertices].count>128||j->tokens[faces].count<4||j->tokens[faces].count>256)return reject(c,"Hull vertices and faces required");
 h->vertexCount=j->tokens[vertices].count;h->faceCount=j->tokens[faces].count;t=vertices+1;
 for(uint32_t i=0;i<h->vertexCount;i++){double v[3];if(!row(j,t,v,3))return reject(c,"Hull vertex row");h->vertices[i]=nrV(v[0],v[1],v[2]);t=j->tokens[t].next;}
 t=faces+1;for(uint32_t i=0;i<h->faceCount;i++){double v[3];if(!row(j,t,v,3))return reject(c,"Hull face row");for(int k=0;k<3;k++){if(!(v[k]>=0&&v[k]<h->vertexCount)||v[k]!=(uint32_t)v[k])return reject(c,"Hull face index");h->faces[i][k]=(uint32_t)v[k];}t=j->tokens[t].next;}
 double v[3];if(!row(j,nrField(j,0,"inertia"),v,3))return reject(c,"Hull principal inertia required");h->inertia=nrV(v[0],v[1],v[2]);
 t=nrField(j,0,"centerOfMass");if(t>=0){if(!row(j,t,v,3))return reject(c,"Hull center of mass");h->centerOfMass=nrV(v[0],v[1],v[2]);}
 t=nrField(j,0,"angularVelocity");if(t>=0){if(!row(j,t,v,3))return reject(c,"Hull angular velocity");h->angularVelocity=nrV(v[0],v[1],v[2]);}
 t=nrField(j,0,"orientation");if(t>=0&&!row(j,t,h->orientation,4))return reject(c,"Hull orientation");
 double out[5];if(nrHullImmersion((const double*)h->vertices,h->vertexCount,&h->faces[0][0],h->faceCount,-1000000,out,5)!=1)return reject(c,"Hull must be closed convex outward mesh");h->volume=out[0];
 if(!valid(h))return reject(c,"Invalid retained hull settings");return 0;
}
int nrFloatHullShape(const Json*j){
 int op=nrField(j,0,"op");if(!nrEqual(j,op,"float-hull")&&!nrEqual(j,op,"remove-float-hull"))return 0;
 double id;if(!nrNumber(j,nrField(j,0,"id"),&id)||id<1||id>65535||id!=(uint32_t)id)return 0;
 if(nrEqual(j,op,"remove-float-hull"))return nrAllowed(j,0,"op id");
 FloatHull h;return parseHull(0,j,&h)==0;
}
int nrFloatHullCommand(NrContext*c,State*s,const Json*j){
 double id;int slot=-1;if(!nrNumber(j,nrField(j,0,"id"),&id)||id<1||id>65535||id!=(uint32_t)id)return reject(c,"Hull body id required");
 for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used&&s->floatBodies[i].id==(uint32_t)id)slot=i;
 if(slot<0)return reject(c,"Hull requires retained float body");
 if(nrEqual(j,nrField(j,0,"op"),"remove-float-hull")){if(!nrAllowed(j,0,"op id"))return reject(c,"Unknown hull removal field");memset(&s->floatHulls[slot],0,sizeof(FloatHull));return 0;}
 FloatHull h;if(parseHull(c,j,&h)<0)return -1;s->floatHulls[slot]=h;return 0;
}

static Vec3 rotate(const FloatHull*h,Vec3 v,int inverse){
 Vec3 q=nrV(h->orientation[0],h->orientation[1],h->orientation[2]);if(inverse)q=nrScale(q,-1);
 Vec3 t=nrScale(nrCross(q,v),2);return nrAdd(v,nrAdd(nrScale(t,h->orientation[3]),nrCross(q,t)));
}
Vec3 nrFloatHullVertex(const FloatBody*b,const FloatHull*h,uint32_t index){return nrAdd(b->position,rotate(h,nrSub(h->vertices[index],h->centerOfMass),0));}
int nrFloatHullTick(State*s,int slot){
 FloatBody*b=&s->floatBodies[slot];FloatHull*h=&s->floatHulls[slot];const double dt=1.0/120;
 Vec3 vertices[128];for(uint32_t k=0;k<h->vertexCount;k++)vertices[k]=nrFloatHullVertex(b,h,k);
 b->normal=nrV(0,1,0);b->immersion=b->buoyantForce=0;
 Vec3 torque=nrV(0,0,0),waterVelocity=nrV(0,0,0);double sample[5];
 double water[256][9];uint32_t waterCount=0;
 for(int k=0;k<s->meshCount;k++)if(s->geometry.triangleSurfaces[k]==(int)b->surfaceId){
  /* Extruded flow sides and bottoms close collision volume, but only its
   * top partitions the free surface used for immersed vertical columns. */
  if(s->flowThicknessTriangles[k].role&&s->flowThicknessTriangles[k].role!=2)continue;
  Triangle t=s->mesh[k];if(nrFlowThicknessTriangleAt(s,k,s->timeUs,&t)==2)continue;nrDisplaceSurfaceTriangle(s,k,&t);
  Vec3 n=nrCross(nrSub(t.b,t.a),nrSub(t.c,t.a));if(nrAbs(n.y)<=1e-12)continue;
  if(waterCount>=256)return 0; /* Reject before writing past the query capacity. */
  double row[9]={t.a.x,t.a.y,t.a.z,t.b.x,t.b.y,t.b.z,t.c.x,t.c.y,t.c.z};memcpy(water[waterCount++],row,sizeof(row));
 }
 if(waterCount){
  double out[5];if(nrHullMeshImmersion((const double*)vertices,h->vertexCount,&h->faces[0][0],h->faceCount,&water[0][0],waterCount,out,5)!=1)return 0;
  b->immersion=nrClamp(out[1]/h->volume,0,1);b->buoyantForce=b->density*b->gravity*out[1];
  Vec3 offset=nrSub(nrV(out[2],out[3],out[4]),b->position);torque=rotate(h,nrCross(offset,nrV(0,b->buoyantForce,0)),1);
  if(nrWaterHeight(s,b->surfaceId,b->position.x,b->position.z,sample)){b->normal=nrV(sample[1],sample[2],sample[3]);waterVelocity.y=sample[4];}
 }

 double drag=b->drag*b->immersion*dt;
 Vec3 acceleration=nrV(0,b->buoyantForce/b->mass-b->gravity,0);
 Vec3 freeVelocity=nrAdd(b->velocity,nrScale(acceleration,dt));int coupled=nrSurfaceFluidExchange(s,b,freeVelocity,dt);if(coupled<0)return 0;
 if(!coupled)b->velocity=nrScale(nrAdd(freeVelocity,nrScale(waterVelocity,drag)),1/(1+drag));
 b->position=nrAdd(b->position,nrScale(b->velocity,dt));
 Vec3 w=h->angularVelocity,momentum=nrV(h->inertia.x*w.x,h->inertia.y*w.y,h->inertia.z*w.z);
 Vec3 angularForce=nrSub(torque,nrCross(w,momentum));
 Vec3 angularAcceleration=nrV(angularForce.x/h->inertia.x,angularForce.y/h->inertia.y,angularForce.z/h->inertia.z);
 Vec3 freeOmega=nrAdd(w,nrScale(angularAcceleration,dt));
 SurfaceFluidAngular*angular=&s->angularFluids[b->surfaceId-1];
 if(angular->used&&s->surfaceFluids[b->surfaceId-1].used==1){
  Vec3 rates=nrScale(h->inertia,b->drag*b->immersion);
  if(!nrAngularFluidRecordExchange(angular,h->inertia,freeOmega,rates,dt,h->orientation,&h->angularVelocity))return 0;
 }else h->angularVelocity=nrScale(freeOmega,1/(1+drag));
 /* q * (omega,0): angular velocity is in the local principal frame. */
 w=h->angularVelocity;Vec3 q=nrV(h->orientation[0],h->orientation[1],h->orientation[2]);double scalar=h->orientation[3];
 Vec3 delta=nrAdd(nrScale(w,scalar),nrCross(q,w));q=nrAdd(q,nrScale(delta,.5*dt));scalar-=.5*dt*nrDot(nrV(h->orientation[0],h->orientation[1],h->orientation[2]),w);
 double norm=nrSqrt(nrDot(q,q)+scalar*scalar);if(!(norm>0&&norm<=1e12)||!vectorValid(h->angularVelocity,1000))return 0;
 h->orientation[0]=q.x/norm;h->orientation[1]=q.y/norm;h->orientation[2]=q.z/norm;h->orientation[3]=scalar/norm;
 return 1;
}
int nrFloatHull(const NrContext*c,uint32_t id,double*out,uint32_t capacity){
 if(!c||c->state.magic!=NR_MAGIC||id<1||id>65535||!out||capacity<14||((uintptr_t)out%8)||!nrExternalOutput(c,out,14*sizeof(double)))return -1;
 for(int i=0;i<NR_FLOAT_BODIES;i++)if(c->state.floatBodies[i].used&&c->state.floatBodies[i].id==id){
  const FloatHull*h=&c->state.floatHulls[i];if(!h->used)return 0;
  double row[14]={h->orientation[0],h->orientation[1],h->orientation[2],h->orientation[3],h->angularVelocity.x,h->angularVelocity.y,h->angularVelocity.z,h->inertia.x,h->inertia.y,h->inertia.z,h->centerOfMass.x,h->centerOfMass.y,h->centerOfMass.z,h->volume};memcpy(out,row,sizeof(row));return 1;
 }
 return 0;
}
int nrFloatHullNumberValid(const Value*v,double x){
 if(v->bindingFamily!=18||!nrResourceBindingShapeValid(v))return 0;
 if(!strcmp(v->field,"hull.angularVelocity.x")||!strcmp(v->field,"hull.angularVelocity.y")||!strcmp(v->field,"hull.angularVelocity.z"))return x>=-1000&&x<=1000;
 if(!strcmp(v->field,"hull.inertia.x")||!strcmp(v->field,"hull.inertia.y")||!strcmp(v->field,"hull.inertia.z"))return x>=.001&&x<=1e12;
 return 0;
}
int nrBindFloatHullValue(State*s,const Value*v,double x){
 if(!nrFloatHullNumberValid(v,x))return 0;
 for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used&&s->floatBodies[i].id==(uint32_t)v->bindingId){
  FloatHull*h=&s->floatHulls[i];if(!h->used)return 0;
  if(!strcmp(v->field,"hull.angularVelocity.x"))h->angularVelocity.x=x;
  else if(!strcmp(v->field,"hull.angularVelocity.y"))h->angularVelocity.y=x;
  else if(!strcmp(v->field,"hull.angularVelocity.z"))h->angularVelocity.z=x;
  else if(!strcmp(v->field,"hull.inertia.x"))h->inertia.x=x;
  else if(!strcmp(v->field,"hull.inertia.y"))h->inertia.y=x;
  else if(!strcmp(v->field,"hull.inertia.z"))h->inertia.z=x;
  else return 0;
  return 1;
 }
 return 0;
}
