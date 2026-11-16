#include "internal.h"
/* Disjoint vertical triangle columns partition a piecewise planar surface.
 * Each column clips one convex hull by three vertical sides and its water face.
 * Retaining every oriented cap makes signed volume/moment integration closed. */
typedef struct {Vec3 ordinary[256][8],caps[4][132];Vec3*face[260];int count[260],faces,ordinaryFaces;} HullPoly;
static int same(Vec3 a,Vec3 b){Vec3 d=nrSub(a,b);return nrDot(d,d)<=1e-20;}
static int capBefore(Vec3 a,Vec3 b,Vec3 center,Vec3 u,Vec3 v){
 a=nrSub(a,center);b=nrSub(b,center);double ax=nrDot(a,u),ay=nrDot(a,v),bx=nrDot(b,u),by=nrDot(b,v);
 int ah=ay>0||(ay==0&&ax>=0),bh=by>0||(by==0&&bx>=0);return ah!=bh?ah>bh:ax*by-ay*bx>0;
}
static int clip(HullPoly*p,Vec3 point,Vec3 normal,int plane){
 Vec3 cap[132],polygon[132];int capCount=0;
 for(int f=0;f<p->faces;f++){
  int n=0,old=p->count[f];Vec3*face=p->face[f];
  for(int k=0;k<old;k++){
   Vec3 a=face[k],b=face[(k+1)%old];double da=nrDot(normal,nrSub(a,point)),db=nrDot(normal,nrSub(b,point));int inside=da<=0,next=db<=0;
   if(inside){if(n>=132)return 0;polygon[n++]=a;}
   if(inside!=next){
    Vec3 hit=nrAdd(a,nrScale(nrSub(b,a),da/(da-db)));hit=nrSub(hit,nrScale(normal,nrDot(normal,nrSub(hit,point))));
    if(n>=132)return 0;polygon[n++]=hit;int duplicate=0;for(int j=0;j<capCount;j++)if(same(cap[j],hit))duplicate=1;
    if(!duplicate){if(capCount>=132)return 0;cap[capCount++]=hit;}
   }
  }
  /* An original triangle gains at most one vertex per clipping plane. */
  if(f<p->ordinaryFaces&&n>8)return 0;p->count[f]=n;if(n)memcpy(face,polygon,n*sizeof(Vec3));
 }
 if(capCount>=3){
  Vec3 center=nrV(0,0,0);for(int i=0;i<capCount;i++)center=nrAdd(center,nrScale(cap[i],1.0/capCount));
  Vec3 axis=nrAbs(normal.x)<.8?nrV(1,0,0):nrV(0,1,0),u=nrNormal(nrCross(axis,normal)),v=nrCross(normal,u);
  for(int i=1;i<capCount;i++){Vec3 key=cap[i];int j=i;while(j>0&&capBefore(key,cap[j-1],center,u,v)){cap[j]=cap[j-1];j--;}cap[j]=key;}
  p->face[p->faces]=p->caps[plane];p->count[p->faces]=capCount;memcpy(p->caps[plane],cap,capCount*sizeof(Vec3));p->faces++;
 }
 return 1;
}
static int column(const double*vertices,const uint32_t*faces,uint32_t triangles,Triangle water,double*out){
 HullPoly p;memset(&p,0,sizeof(p));p.faces=p.ordinaryFaces=triangles;
 for(uint32_t i=0;i<triangles;i++){p.face[i]=p.ordinary[i];p.count[i]=3;for(int k=0;k<3;k++){uint32_t id=faces[3*i+k];p.face[i][k]=nrV(vertices[3*id],vertices[3*id+1],vertices[3*id+2]);}}
 Vec3 corners[3]={water.a,water.b,water.c},normal=nrCross(nrSub(water.b,water.a),nrSub(water.c,water.a));if(normal.y<0){Vec3 swap=corners[1];corners[1]=corners[2];corners[2]=swap;normal=nrScale(normal,-1);}
 for(int k=0;k<3;k++){Vec3 edge=nrSub(corners[(k+1)%3],corners[k]),side=nrNormal(nrV(-edge.z,0,edge.x));if(!clip(&p,corners[k],side,k))return 0;}
 if(!clip(&p,corners[0],nrNormal(normal),3))return 0;
 Vec3 reference=nrV(vertices[0],vertices[1],vertices[2]),moment=nrV(0,0,0);double volume=0;
 for(int f=0;f<p.faces;f++)for(int k=1;k+1<p.count[f];k++){
  Vec3 a=p.face[f][0],b=p.face[f][k],c=p.face[f][k+1];double det=nrDot(nrSub(a,reference),nrCross(nrSub(b,reference),nrSub(c,reference)));volume+=det;moment=nrAdd(moment,nrScale(nrAdd(reference,nrAdd(a,nrAdd(b,c))),det));
 }
 if(!(volume>=-1e-8))return 0;out[0]=volume>0?volume/6:0;out[1]=moment.x/24;out[2]=moment.y/24;out[3]=moment.z/24;return 1;
}
static int separate(Triangle a,Triangle b){
 Vec3 first[3]={a.a,a.b,a.c},second[3]={b.a,b.b,b.c};
 for(int group=0;group<2;group++){Vec3*poly=group?second:first;for(int k=0;k<3;k++){
  Vec3 edge=nrSub(poly[(k+1)%3],poly[k]),axis=nrNormal(nrV(-edge.z,0,edge.x));double amin=1e30,amax=-1e30,bmin=1e30,bmax=-1e30;
  for(int j=0;j<3;j++){double x=nrDot(axis,first[j]),y=nrDot(axis,second[j]);if(x<amin)amin=x;if(x>amax)amax=x;if(y<bmin)bmin=y;if(y>bmax)bmax=y;}
  if(amax<=bmin+1e-10||bmax<=amin+1e-10)return 1;
 }}return 0;
}
int nrHullMeshImmersion(const double*vertices,uint32_t count,const uint32_t*faces,uint32_t triangles,const double*water,uint32_t waterCount,double*out,uint32_t capacity){
 if(!water||((uintptr_t)water%8)||!out||((uintptr_t)out%8)||capacity<5||waterCount<1||waterCount>256)return -1;
 double full[5];if(nrHullImmersion(vertices,count,faces,triangles,-1000000,full,5)!=1)return -1;
 Triangle surface[256];
 for(uint32_t i=0;i<waterCount;i++){
  for(int k=0;k<9;k++)if(!(water[9*i+k]>=-1000000&&water[9*i+k]<=1000000))return -1;
  surface[i]=(Triangle){nrV(water[9*i],water[9*i+1],water[9*i+2]),nrV(water[9*i+3],water[9*i+4],water[9*i+5]),nrV(water[9*i+6],water[9*i+7],water[9*i+8]),0,1};
  Vec3 n=nrCross(nrSub(surface[i].b,surface[i].a),nrSub(surface[i].c,surface[i].a));if(!(nrAbs(n.y)>1e-12))return -1;
  for(uint32_t j=0;j<i;j++)if(!separate(surface[i],surface[j]))return -1;
 }
 double row[5]={full[0],0,0,0,0};Vec3 moment=nrV(0,0,0);
 for(uint32_t i=0;i<waterCount;i++){double part[4];if(!column(vertices,faces,triangles,surface[i],part))return -1;row[1]+=part[0];moment=nrAdd(moment,nrV(part[1],part[2],part[3]));}
 if(!(row[1]>=0&&row[1]<=row[0]*(1+1e-8)))return -1;
 if(row[1]>0){row[2]=moment.x/row[1];row[3]=moment.y/row[1];row[4]=moment.z/row[1];}
 for(int k=0;k<5;k++)if(!(row[k]>=-1e30&&row[k]<=1e30))return -1;
 memcpy(out,row,sizeof(row));return 1;
}
