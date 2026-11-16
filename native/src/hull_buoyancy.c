#include "internal.h"
/* Gravity acts at the center of mass; hydrostatic lift acts at the exact
 * submerged volume centroid. Their moment is expressed about center of mass. */
int nrHullBuoyancyPlane(const double*vertices,uint32_t count,const uint32_t*faces,uint32_t triangles,const double*point,const double*normal,double density,double gravity,double mass,const double*center,double*out,uint32_t capacity){
    if(!center||!out||((uintptr_t)center%8)||((uintptr_t)out%8)||capacity<11||
       !(density>=0&&density<=100000)||!(gravity>=0&&gravity<=256)||!(mass>=.001&&mass<=1000000))return -1;
    Vec3 origin=nrV(center[0],center[1],center[2]);
    if(!(origin.x>=-1000000&&origin.x<=1000000&&origin.y>=-1000000&&origin.y<=1000000&&origin.z>=-1000000&&origin.z<=1000000))return -1;
    double row[11]={0};if(nrHullImmersionPlane(vertices,count,faces,triangles,point,normal,row,5)!=1)return -1;
    double lift=density*gravity*row[1];Vec3 torque=nrCross(nrSub(nrV(row[2],row[3],row[4]),origin),nrV(0,lift,0));
    row[6]=lift-mass*gravity;row[8]=torque.x;row[9]=torque.y;row[10]=torque.z;
    for(int i=0;i<11;i++)if(!(row[i]>=-1e30&&row[i]<=1e30))return -1;
    memcpy(out,row,sizeof(row));return 1;
}

int nrHullBuoyancy(const double*vertices,uint32_t count,const uint32_t*faces,uint32_t triangles,double height,double density,double gravity,double mass,const double*center,double*out,uint32_t capacity){
    double point[3]={0,height,0},normal[3]={0,1,0};
    return nrHullBuoyancyPlane(vertices,count,faces,triangles,point,normal,density,gravity,mass,center,out,capacity);
}
