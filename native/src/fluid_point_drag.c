#include "internal.h"

/* Exact linear point drag for a frozen contact radius and isotropic reservoir
 * inertia. Parallel and perpendicular modes have different effective mass;
 * perpendicular reaction transfers both translation and angular momentum. */
int nrFluidPointDragExchange(double bodyMass,double waterMass,double inertia,double conductance,double seconds,Vec3 bodyVelocity,Vec3 waterVelocity,Vec3 waterOmega,Vec3 radius,double*out){
 if(!out||((uintptr_t)out%8)||!(inertia>=.001&&inertia<=1e12)||!(bodyMass>=.001&&bodyMass<=1e12&&waterMass>=.001&&waterMass<=1e12&&conductance>=0&&conductance<=1e12&&seconds>=0&&seconds<=86400))return 0;
 Vec3 vectors[4]={bodyVelocity,waterVelocity,waterOmega,radius};for(int k=0;k<4;k++)if(!(vectors[k].x>=-32760&&vectors[k].x<=32760&&vectors[k].y>=-32760&&vectors[k].y<=32760&&vectors[k].z>=-32760&&vectors[k].z<=32760))return 0;
 Vec3 relative=nrSub(bodyVelocity,nrAdd(waterVelocity,nrCross(waterOmega,radius)));
 double squared=nrDot(radius,radius);Vec3 parallel=squared>0?nrScale(radius,nrDot(relative,radius)/squared):relative;
 Vec3 modes[2]={parallel,nrSub(relative,parallel)},impulse=nrV(0,0,0);double dissipated=0;
 for(int mode=0;mode<2;mode++){
  /* Derived inverse mass has no authored mass floor. Computing the reduced
   * mass directly also avoids multiplying extreme effective masses. */
  double inverse=1/bodyMass+1/waterMass+(mode?squared/inertia:0),reduced=1/inverse;
  double fraction=nrDragResponseFraction(conductance*seconds*inverse);
  impulse=nrAdd(impulse,nrScale(modes[mode],reduced*fraction));
  dissipated+=.5*reduced*nrDot(modes[mode],modes[mode])*fraction*(2-fraction);
 }
 Vec3 body=nrSub(bodyVelocity,nrScale(impulse,1/bodyMass)),water=nrAdd(waterVelocity,nrScale(impulse,1/waterMass));
 Vec3 omega=nrAdd(waterOmega,nrScale(nrCross(radius,impulse),1/inertia));
 double row[13]={body.x,body.y,body.z,water.x,water.y,water.z,omega.x,omega.y,omega.z,impulse.x,impulse.y,impulse.z,dissipated};
 for(int k=0;k<13;k++)if(!(row[k]>=-1e30&&row[k]<=1e30))return 0;
 memcpy(out,row,sizeof(row));return 1;
}
