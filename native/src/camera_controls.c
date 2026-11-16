#include "camera_controls.h"
#include "original_math.h"
/* World orbit uses a single rigid transform. Local look uses the current mount
 * axes; it never derives a translation from the current pointer coordinate. */
static double sn(double d){return nrOriginalSin(d*NR_PI/180);}
static double cs(double d){return nrOriginalCos(d*NR_PI/180);}
static double wrap(double d){return d-360*nrFloor((d+180)/360);}
static int bounded(double v,double lo,double hi){return v>=lo&&v<=hi;}
static int validVec(Vec3 v,double n){return bounded(v.x,-n,n)&&bounded(v.y,-n,n)&&bounded(v.z,-n,n);}
static void basis(const Camera*c,Vec3*r,Vec3*u,Vec3*f){
 double cy=cs(c->yaw),sy=sn(c->yaw),cp=cs(c->pitch),sp=sn(c->pitch),cr=cs(c->roll),sr=sn(c->roll);
 Vec3 a=nrV(cy,0,sy),b=nrV(-sy*sp,cp,cy*sp);*f=nrV(sy*cp,sp,-cy*cp);*r=nrAdd(nrScale(a,cr),nrScale(b,sr));*u=nrSub(nrScale(b,cr),nrScale(a,sr));
}
static Vec3 cross(Vec3 a,Vec3 b){return nrV(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);}
static Vec3 rotated(Vec3 v,Vec3 axis,double degrees){double c=cs(degrees),s=sn(degrees);return nrAdd(nrAdd(nrScale(v,c),nrScale(cross(axis,v),s)),nrScale(axis,nrDot(axis,v)*(1-c)));}
static Vec3 xyz(Vec3 v,Vec3 d){v=rotated(v,nrV(1,0,0),d.x);v=rotated(v,nrV(0,1,0),d.y);return rotated(v,nrV(0,0,1),d.z);}
static void orientation(Camera*c,Vec3 right,Vec3 forward){
 double horizontal=nrOriginalHypot(forward.x,forward.z,0),yaw=c->yaw;
 if(horizontal>1e-12)yaw=nrOriginalAtan2(forward.x,-forward.z)*180/NR_PI;
 c->yaw=wrap(yaw);c->pitch=nrOriginalAtan2(forward.y,horizontal)*180/NR_PI;
 Vec3 a=nrV(cs(c->yaw),0,sn(c->yaw));Vec3 b=nrV(-sn(c->yaw)*sn(c->pitch),cs(c->pitch),cs(c->yaw)*sn(c->pitch));
 c->roll=wrap(nrOriginalAtan2(nrDot(right,b),nrDot(right,a))*180/NR_PI);
}
void nrCameraRotatePose(Camera*c,Vec3 pivot,Vec3 degrees,int position,int rotation){
 Vec3 r,u,f;basis(c,&r,&u,&f);if(position)c->position=nrAdd(pivot,xyz(nrSub(c->position,pivot),degrees));if(rotation)orientation(c,xyz(r,degrees),xyz(f,degrees));
}
static void look(Camera*c,int axis,double degrees){Vec3 r,u,f;basis(c,&r,&u,&f);Vec3 a=axis==0?r:axis==1?u:nrScale(f,-1);orientation(c,rotated(r,a,degrees),rotated(f,a,degrees));}
static Vec3 local(const Camera*c,Vec3 v){Vec3 r,u,f;basis(c,&r,&u,&f);return nrAdd(nrAdd(nrScale(r,v.x),nrScale(u,v.y)),nrScale(f,v.z));}
static Vec3 followTarget(const State*s,const CameraControls*k,uint64_t us){if(k->followKind){int slot=nrFindNode(s,(int)k->followId);if(slot>=0)return nrNodeAt(&s->nodes[slot],us);}return k->followPoint;}
static Camera composeHead(Camera body,const CameraControls*k){
 Vec3 r,u,f,hr,hu,hf;basis(&body,&r,&u,&f);body.position=nrAdd(body.position,local(&body,k->headPosition));
 Camera head=body;head.yaw=k->headRotation.y;head.pitch=k->headRotation.x;head.roll=k->headRotation.z;basis(&head,&hr,&hu,&hf);
 Vec3 right=nrAdd(nrAdd(nrScale(r,hr.x),nrScale(u,hr.y)),nrScale(f,-hr.z));Vec3 forward=nrAdd(nrAdd(nrScale(r,hf.x),nrScale(u,hf.y)),nrScale(f,-hf.z));orientation(&body,right,forward);return body;
}
static Camera followCarrier(const State*s,const CameraControls*k,Camera body,uint64_t us){
 if(k->rig==4){Vec3 target=followTarget(s,k,us);body.position=nrAdd(body.position,nrSub(target,k->followReference));if(k->followTrack){Vec3 d=nrSub(target,body.position);double h=nrOriginalHypot(d.x,d.z,0);if(h>1e-12||nrAbs(d.y)>1e-12){body.yaw=nrOriginalAtan2(d.x,-d.z)*180/NR_PI;body.pitch=nrOriginalAtan2(d.y,h)*180/NR_PI;}}}
 return body;
}
Camera nrCameraControlsCompose(const State*s,Camera body,uint64_t us){const CameraControls*k=&s->cameraControls;if(!k->configured)return body;return composeHead(followCarrier(s,k,body,us),k);}
/* Wheel supplies Z: default orbit dollies; explicit orbit-z remains available. */
static void axes(CameraControls*k){
 int pan=k->mode==1,fly=k->mode==2;for(int i=0;i<3;i++){CameraAxisControl*a=&k->axes[i];memset(a,0,sizeof(*a));a->enabled=1;a->sensitivity=pan?(i==0?.5:i==1?.6:2):.65;a->invert=pan?i==0:i<2;a->action=pan?4+i:fly?(i==0?8:i==1?7:9):(i==0?2:i==1?1:6);}
}
static void defaults(CameraControls*k,const Camera*body){memset(k,0,sizeof(*k));k->configured=1;k->followTrack=1;k->craneBoom=body->position;k->followOffset=body->position;axes(k);}
static int reject(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static int object(const Json*j,int t,const char*fields){return t>=0&&j->tokens[t].type==J_OBJECT&&nrAllowed(j,t,fields);}
static int number(const Json*j,int t,const char*key,double*out,double lo,double hi){int f=nrField(j,t,key);return f<0||(nrNumber(j,f,out)&&bounded(*out,lo,hi));}
static int boolean(const Json*j,int t,const char*key,uint32_t*out){int f=nrField(j,t,key),v;if(f<0)return 1;if(!nrBoolean(j,f,&v))return 0;*out=(uint32_t)v;return 1;}
static int vector(const Json*j,int t,Vec3*out,double limit){if(t<0)return 1;if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=3)return 0;double*v[3]={&out->x,&out->y,&out->z};for(int i=0,q=t+1;i<3;i++,q=j->tokens[q].next)if(!nrNumber(j,q,v[i])||!bounded(*v[i],-limit,limit))return 0;return 1;}
static int choice(const Json*j,int p,const char*key,const char*const*names,int count,uint32_t*out){int t=nrField(j,p,key);if(t<0)return 1;for(int i=0;i<count;i++)if(nrEqual(j,t,names[i])){*out=i;return 1;}return 0;}
static const char*const rigs[]={"orbit","head","dolly","crane","follow","spacecraft"};
static const char*const modes[]={"orbit","pan","fly"};
static const char*const targets[]={"body","head"};
static const char*const actions[]={"disabled","orbit-x","orbit-y","orbit-z","pan-x","pan-y","pan-z","look-x","look-y","look-z"};
int nrCameraControlsCommand(NrContext*c,State*s,const Json*j){
 if(s->schema<NR_STATE_SCHEMA_CAMERA_CONTROLS)return reject(c,"Camera controls require current schema");
 int op=nrField(j,0,"op");CameraControls*k=&s->cameraControls;
 if(nrEqual(j,op,"camera-input")){Vec3 delta={0};uint32_t pan=0;if(!object(j,0,"op delta pan")||!k->configured||nrField(j,0,"delta")<0||!vector(j,nrField(j,0,"delta"),&delta,100000)||!boolean(j,0,"pan",&pan))return reject(c,"Invalid camera input");nrCameraControlInput(s,delta.x,delta.y,delta.z,(int)pan);return 0;}
 if(!nrEqual(j,op,"camera-controls")||!object(j,0,"op enabled rig mode inputTarget inputAxes head crane follow anchor"))return reject(c,"Unknown camera controls field");
 uint32_t enabled=1;if(!boolean(j,0,"enabled",&enabled))return reject(c,"Invalid camera controls enabled");
 if(!enabled){if(!nrAllowed(j,0,"op enabled"))return reject(c,"Disabled camera controls cannot configure fields");Camera composed=nrCameraAt(s),before=nrCameraCarrierAt(s);memset(k,0,sizeof(*k));nrCameraManualPose(s,&before,&composed);return 0;}
 Camera before=nrCameraCarrierAt(s),body=before,effective=k->configured?followCarrier(s,k,before,s->timeUs):before;uint32_t oldRig=k->rig;int fresh=!k->configured;if(fresh)defaults(k,&body);
 int hasRig=nrField(j,0,"rig")>=0,hasMode=nrField(j,0,"mode")>=0;
 if(!choice(j,0,"rig",rigs,6,&k->rig))return reject(c,"Unknown camera rig");
 if(hasRig&&oldRig==4&&k->rig!=4)body=effective;
 if(hasRig){k->mode=k->rig==1||k->rig==5?2:k->rig==2||k->rig==4?1:0;k->inputTarget=k->rig==5?1:0;}
 if(!choice(j,0,"mode",modes,3,&k->mode)||!choice(j,0,"inputTarget",targets,2,&k->inputTarget))return reject(c,"Invalid camera mode or input target");
 if(hasRig||hasMode)axes(k);
 int axis=nrField(j,0,"inputAxes");if(axis>=0){if(!object(j,axis,"x y z"))return reject(c,"Invalid camera axes");const char*keys[]={"x","y","z"};for(int i=0;i<3;i++){int t=nrField(j,axis,keys[i]);if(t<0)continue;CameraAxisControl*a=&k->axes[i];if(!object(j,t,"action enabled invert sensitivity")||!choice(j,t,"action",actions,10,&a->action)||!boolean(j,t,"enabled",&a->enabled)||!boolean(j,t,"invert",&a->invert)||!number(j,t,"sensitivity",&a->sensitivity,0,1000))return reject(c,"Invalid camera axis");}}
 int head=nrField(j,0,"head");if(head>=0&&(!object(j,head,"position rotation")||!vector(j,nrField(j,head,"position"),&k->headPosition,100000)||!vector(j,nrField(j,head,"rotation"),&k->headRotation,36000)))return reject(c,"Invalid camera head");
 int crane=nrField(j,0,"crane");if(crane>=0){if(!object(j,crane,"pivot boom")||!vector(j,nrField(j,crane,"pivot"),&k->cranePivot,100000)||!vector(j,nrField(j,crane,"boom"),&k->craneBoom,100000))return reject(c,"Invalid camera crane");if(k->rig==3)body.position=nrAdd(k->cranePivot,k->craneBoom);}
 else if(hasRig&&k->rig==3)k->craneBoom=nrSub(body.position,k->cranePivot);
 int follow=nrField(j,0,"follow"),targetChanged=0,offsetChanged=0;
 if(follow>=0){if(!object(j,follow,"target offset track")||!vector(j,nrField(j,follow,"offset"),&k->followOffset,100000)||!boolean(j,follow,"track",&k->followTrack))return reject(c,"Invalid follow camera");offsetChanged=nrField(j,follow,"offset")>=0;int t=nrField(j,follow,"target");if(t>=0){targetChanged=1;int kind=nrField(j,t,"kind");if(kind<0)return reject(c,"Follow target kind required");if(nrEqual(j,kind,"point")){if(!object(j,t,"kind point")||nrField(j,t,"point")<0||!vector(j,nrField(j,t,"point"),&k->followPoint,100000))return reject(c,"Invalid follow point");k->followKind=0;k->followId=0;}else if(nrEqual(j,kind,"node")){double id=0;if(!object(j,t,"kind id")||nrField(j,t,"id")<0||!number(j,t,"id",&id,1,65535)||id!=nrFloor(id)||nrFindNode(s,(int)id)<0)return reject(c,"Follow node not found");k->followKind=1;k->followId=(uint32_t)id;k->followPoint=nrV(0,0,0);}else return reject(c,"Unknown follow target");}}
 if(k->rig==4&&(hasRig||targetChanged||offsetChanged)){Vec3 target=followTarget(s,k,s->timeUs);if(!offsetChanged)k->followOffset=nrSub(effective.position,target);k->followReference=target;body.position=nrAdd(target,k->followOffset);}
 int anchor=nrField(j,0,"anchor");if(anchor>=0){if(j->tokens[anchor].type==J_NULL){k->anchorEnabled=0;k->anchor=nrV(0,0,0);}else{if(!vector(j,anchor,&k->anchor,1e9))return reject(c,"Invalid camera anchor");k->anchorEnabled=1;}}
 if(!validVec(body.position,100000))return reject(c,"Camera carrier position range");
 nrCameraManualPose(s,&before,&body);return 0;
}
int nrValidCameraControls(const State*s){
 const CameraControls*k=&s->cameraControls;if(!k->configured){CameraControls zero={0};return !memcmp(k,&zero,sizeof(zero));}
 if(s->schema<NR_STATE_SCHEMA_CAMERA_CONTROLS||k->configured!=1||k->rig>5||k->mode>2||k->inputTarget>1||k->followKind>1||k->anchorEnabled>1||k->followTrack>1)return 0;
 for(int i=0;i<3;i++){const CameraAxisControl*a=&k->axes[i];if(a->action>9||a->enabled>1||a->invert>1||a->reserved||!bounded(a->sensitivity,0,1000))return 0;}
 if(!validVec(k->headPosition,100000)||!validVec(k->headRotation,36000)||!validVec(k->cranePivot,100000)||!validVec(k->craneBoom,100000)||!validVec(k->followPoint,100000)||!validVec(k->followOffset,100000)||!validVec(k->followReference,100000)||!validVec(k->anchor,1e9))return 0;
 if(!k->anchorEnabled&&(k->anchor.x||k->anchor.y||k->anchor.z))return 0;
 if(k->followKind){if(k->followId<1||k->followId>65535||nrFindNode(s,(int)k->followId)<0)return 0;}else if(k->followId)return 0;
 return 1;
}
void nrCameraControlInput(State*s,double dx,double dy,double dz,int explicitPan){
 CameraControls*k=&s->cameraControls;if(!k->configured)return;Camera before=nrCameraCarrierAt(s),body=before;double inputs[]={dx,dy,dz};
 OriginalCamera grab=s->originalCamera;Vec3 pivot=k->anchorEnabled?k->anchor:grab.grabActive?grab.grabbed:grab.enabled?grab.target:nrV(0,0,0);
 if(k->rig==3)pivot=k->cranePivot;else if(k->rig==4)pivot=k->followReference;
 int head=k->inputTarget==1&&!explicitPan,owned=nrCameraPathOwned(s);
 if(head){body.yaw=k->headRotation.y;body.pitch=k->headRotation.x;body.roll=k->headRotation.z;body.position=k->headPosition;}
 if(explicitPan){if(k->rig!=1&&!owned){Vec3 d=local(&body,nrV(-dx*.5,dy*.6,dz*2));body.position=nrAdd(body.position,d);if(k->rig==3)k->cranePivot=nrAdd(k->cranePivot,d);}}
 else for(int i=0;i<3;i++){const CameraAxisControl*a=&k->axes[i];if(!a->enabled||!a->action||!inputs[i]||!a->sensitivity)continue;double n=inputs[i]*a->sensitivity*(a->invert?-1:1);int axis=(a->action-1)%3;
  if(a->action<=3){Vec3 degrees=nrV(axis==0?n:0,axis==1?n:0,axis==2?n:0);if(head||k->rig==1)look(&body,axis,n);else nrCameraRotatePose(&body,pivot,degrees,!owned,k->rig!=3);}
  else if(a->action<=6){if((k->rig==1||owned)&&!head)continue;Vec3 v=nrV(axis==0?n:0,axis==1?n:0,axis==2?n:0);body.position=nrAdd(body.position,local(&body,v));if(k->rig==3&&!head)k->cranePivot=nrAdd(k->cranePivot,local(&body,v));}
  else look(&body,axis,n);
 }
 if(head){k->headPosition=body.position;k->headRotation=nrV(body.pitch,body.yaw,body.roll);return;}
 if(k->rig==3&&!owned)k->craneBoom=nrSub(body.position,k->cranePivot);
 if(k->rig==4&&!owned)k->followOffset=nrSub(body.position,k->followReference);
 nrCameraManualPose(s,&before,&body);
 /* Manual edits maintain flight, and the same captured pick remains authoritative
    for the entire pointer gesture. No re-pick occurs after its first input. */
 if(grab.grabActive){s->originalCamera.grabActive=grab.grabActive;s->originalCamera.grabSource=grab.grabSource;s->originalCamera.grabWidth=grab.grabWidth;s->originalCamera.grabHeight=grab.grabHeight;s->originalCamera.grabbed=grab.grabbed;}
}
