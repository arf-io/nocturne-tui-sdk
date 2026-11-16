#include "internal.h"
/* A reference point on the cut plane makes every cap tetrahedron zero-volume.
 * Integrating the clipped oriented boundary therefore needs no invented cap
 * triangulation. Signed tetrahedral first moments provide the exact centroid. */
static double determinant(Vec3 a,Vec3 b,Vec3 c,Vec3 reference){return nrDot(nrSub(a,reference),nrCross(nrSub(b,reference),nrSub(c,reference)));}
int nrHullImmersionPlane(const double*vertices,uint32_t count,const uint32_t*faces,uint32_t triangles,const double*planePoint,const double*planeNormal,double*out,uint32_t capacity){
    if(!vertices||!faces||!out||count<4||count>128||triangles<4||triangles>256||capacity<5||((uintptr_t)vertices%8)||((uintptr_t)faces%4)||((uintptr_t)out%8)||!planePoint||!planeNormal||((uintptr_t)planePoint%8)||((uintptr_t)planeNormal%8))return -1;
    Vec3 plane=nrV(planePoint[0],planePoint[1],planePoint[2]),normal=nrV(planeNormal[0],planeNormal[1],planeNormal[2]);
    if(!(plane.x>=-1000000&&plane.x<=1000000&&plane.y>=-1000000&&plane.y<=1000000&&plane.z>=-1000000&&plane.z<=1000000&&normal.x>=-1000000&&normal.x<=1000000&&normal.y>=-1000000&&normal.y<=1000000&&normal.z>=-1000000&&normal.z<=1000000))return -1;
    double norm=nrSqrt(nrDot(normal,normal));if(!(norm>=1e-12))return -1;normal=nrScale(normal,1/norm);
    Vec3 points[128],reference=nrV(0,0,0);
    for(uint32_t i=0;i<count;i++){
        double x=vertices[3*i],y=vertices[3*i+1],z=vertices[3*i+2];
        if(!(x>=-1000000&&x<=1000000&&y>=-1000000&&y<=1000000&&z>=-1000000&&z<=1000000))return -1;
        points[i]=nrV(x,y,z);reference=nrAdd(reference,nrScale(points[i],1.0/count));
    }
    reference=nrSub(reference,nrScale(normal,nrDot(normal,nrSub(reference,plane))));
    unsigned char used[128]={0};double full=0,submerged=0;Vec3 moment=nrV(0,0,0);
    for(uint32_t i=0;i<triangles;i++){
        uint32_t ids[3]={faces[3*i],faces[3*i+1],faces[3*i+2]};
        for(int k=0;k<3;k++){if(ids[k]>=count||ids[k]==ids[(k+1)%3])return -1;used[ids[k]]=1;}
        Vec3 a=points[ids[0]],b=points[ids[1]],c=points[ids[2]],faceNormal=nrCross(nrSub(b,a),nrSub(c,a));
        double length=nrSqrt(nrDot(faceNormal,faceNormal));if(!(length>1e-12))return -1;
        /* Every vertex lies inside each outward face's supporting half-space. */
        for(uint32_t v=0;v<count;v++)if(nrDot(faceNormal,nrSub(points[v],a))>length*1e-8)return -1;
        /* Require one oppositely oriented counterpart for every indexed edge. */
        for(int edge=0;edge<3;edge++){
            uint32_t from=ids[edge],to=ids[(edge+1)%3];int reverse=0,same=0;
            for(uint32_t other=0;other<triangles;other++)if(other!=i)for(int k=0;k<3;k++){
                uint32_t u=faces[3*other+k],v=faces[3*other+(k+1)%3];
                reverse+=u==to&&v==from;same+=u==from&&v==to;
            }
            if(reverse!=1||same)return -1;
        }
        full+=determinant(a,b,c,points[0]);
        Vec3 original[3]={a,b,c},polygon[4];int n=0;
        for(int k=0;k<3;k++){
            Vec3 from=original[k],to=original[(k+1)%3];double distance=nrDot(normal,nrSub(from,plane)),nextDistance=nrDot(normal,nrSub(to,plane));int inside=distance<=0,next=nextDistance<=0;
            if(inside)polygon[n++]=from;
            if(inside!=next){double fraction=distance/(distance-nextDistance);Vec3 hit=nrAdd(from,nrScale(nrSub(to,from),fraction));hit=nrSub(hit,nrScale(normal,nrDot(normal,nrSub(hit,plane))));polygon[n++]=hit;}
        }
        for(int k=1;k+1<n;k++){
            double volume=determinant(polygon[0],polygon[k],polygon[k+1],reference);submerged+=volume;
            Vec3 sum=nrAdd(reference,nrAdd(polygon[0],nrAdd(polygon[k],polygon[k+1])));moment=nrAdd(moment,nrScale(sum,volume));
        }
    }
    for(uint32_t i=0;i<count;i++)if(!used[i])return -1;
    if(!(full>1e-12)||!(submerged>=-full*1e-8&&submerged<=full*(1+1e-8)))return -1;
    double row[5]={full/6,nrClamp(submerged,0,full)/6,0,0,0};
    if(submerged>0){Vec3 centroid=nrScale(moment,1/(4*submerged));row[2]=centroid.x;row[3]=centroid.y;row[4]=centroid.z;}
    for(int i=0;i<5;i++)if(!(row[i]>=-1e30&&row[i]<=1e30))return -1;
    memcpy(out,row,sizeof(row));return 1;
}

int nrHullImmersion(const double*vertices,uint32_t count,const uint32_t*faces,uint32_t triangles,double height,double*out,uint32_t capacity){
    double point[3]={0,height,0},normal[3]={0,1,0};
    return nrHullImmersionPlane(vertices,count,faces,triangles,point,normal,out,capacity);
}
