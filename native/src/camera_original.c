#include "internal.h"
#include "window_source_math.h"
#include "original_math.h"
#include "camera_controls.h"
#include "scenic_native.h"
#include "scenic_source_raster.h"

static int reject(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static int bounded(double x,double a,double b){return x>=a&&x<=b;}
static int vectorBounded(Vec3 v,double limit){return bounded(v.x,-limit,limit)&&bounded(v.y,-limit,limit)&&bounded(v.z,-limit,limit);}
static double sine(double a){return nrOriginalSin(a);}
static double cosine(double a){return nrOriginalCos(a);}
static double length(Vec3 v){return nrOriginalHypot(v.x,v.y,v.z);}
static double wrap(double x){double v=x+180,q=v/360;v-=360*(q<0?-nrFloor(-q):nrFloor(q));v+=360;v-=360*nrFloor(v/360);return v-180;}
static Camera configured(Camera c){c.yaw=wrap(c.yaw);c.roll=wrap(c.roll);return c;}
static double angle(double y,double x){return nrOriginalAtan2(y,x);}
static double exponential(double x){return nrOriginalExp(x);}
static void basis(const Camera*c,Vec3*r,Vec3*u,Vec3*f){
 double y=c->yaw*NR_PI/180,p=c->pitch*NR_PI/180,a=c->roll*NR_PI/180,cy=cosine(y),sy=sine(y),cp=cosine(p),sp=sine(p),cr=cosine(a),sr=sine(a);
 Vec3 right=nrV(cy,0,sy),up=nrV(-sy*sp,cp,cy*sp);*f=nrV(sy*cp,sp,-cy*cp);*r=nrAdd(nrScale(right,cr),nrScale(up,sr));*u=nrAdd(nrScale(up,cr),nrScale(right,-sr));
}
static double intSin(double a,double k,double t){return nrAbs(k)<1e-10?sine(a)*t:(cosine(a)-cosine(a+k*t))/k;}
static double intCos(double a,double k,double t){return nrAbs(k)<1e-10?cosine(a)*t:(sine(a+k*t)-sine(a))/k;}
static Camera maneuver(Camera c,const OriginalFlightStep*m,double seconds){
 double duration=m->durationUs/1e6,t=nrClamp(seconds,0,duration),u=t/duration,d=m->degrees,rad=NR_PI/180,y=c.yaw*rad,p=c.pitch*rad;
 double ky=(m->kind==1?d:0)*rad/duration,kp=(m->kind==2?nrAbs(d):m->kind==3?-nrAbs(d):0)*rad/duration;
 c.position.x+=.5*(intSin(y+p,ky+kp,t)+intSin(y-p,ky-kp,t))*m->speed;
 c.position.z-=.5*(intCos(y+p,ky+kp,t)+intCos(y-p,ky-kp,t))*m->speed;
 c.position.y+=intSin(p,kp,t)*m->speed;
 c.yaw+=ky*t/rad;c.pitch+=kp*t/rad;
 c.roll+=m->kind==4?d*u:m->kind==1&&m->coordinated?(d>0?1:d<0?-1:0)*m->bank*sine(NR_PI*u):0;
 return c;
}
Camera nrOriginalCameraAtTime(const State*s,uint64_t timeUs){
 const OriginalCamera*a=&s->originalCamera;Camera c=a->origin;
 double t=timeUs>a->startUs?(timeUs-a->startUs)/1e6:0;
 if(a->flightKind==1){for(uint32_t i=0;i<a->stepCount;i++){const OriginalFlightStep*m=&a->steps[i];c=maneuver(c,m,t);if(t<=m->durationUs/1e6)break;t-=m->durationUs/1e6;}return configured(c);}
 if(a->flightKind==2){c.position=nrAdd(c.position,nrScale(a->direction,a->speed*t));return configured(c);}
 if(a->flightKind==3){
  double q=t*2*NR_PI/a->periodSeconds,r=a->orbitMode==0?a->radius:a->orbitMode==1?a->radius+a->radialRate*t:nrClamp(a->radius*exponential(-a->radialRate*t/a->radius),2,1e300);
  c.position=nrAdd(a->orbitTarget,nrScale(nrAdd(nrScale(a->radial,cosine(q)),nrScale(a->tangent,sine(q))),r));
  c.position.y=a->orbitTarget.y+r*a->radial.y*cosine(q);
  Vec3 d=nrSub(a->orbitTarget,c.position);c.yaw=angle(d.x,-d.z)/(NR_PI/180);c.pitch=angle(d.y,nrOriginalHypot(d.x,d.z,0))/(NR_PI/180);
  c.roll+=(a->bank-c.roll)*sine(nrClamp(t,0,1)*NR_PI/2);return configured(c);
 }
 return s->camera;
}
Camera nrOriginalCameraAt(const State*s){return nrOriginalCameraAtTime(s,s->timeUs);}
/* Every path that ends pointer capture releases its camera grab: a pick never
 * outlives its gesture (pointer cancellation releases the grab). */
void nrPointerRelease(State*s){s->pointerActive=0;s->originalCamera.grabActive=0;if(!s->originalCamera.enabled)memset(&s->originalCamera,0,sizeof(s->originalCamera));}
void nrOriginalCameraStop(State*s){s->originalCamera.flightKind=0;s->originalCamera.stepCount=0;s->originalCamera.grabActive=0;if(!s->originalCamera.enabled)memset(&s->originalCamera,0,sizeof(s->originalCamera));}
/* Manual view controls edit the camera overlay while the authored flight clock,
 * heading and manoeuvre sequence continue. Only brake stops the sequence. */
void nrCameraManualPose(State*s,const Camera*before,const Camera*desired){
 Camera q=*desired;Vec3 delta=nrSub(q.position,before->position);OriginalCamera*a=&s->originalCamera;
 if(s->flight.count||a->flightKind){Camera*origin=a->flightKind?&a->origin:&s->flight.origin;origin->position=nrAdd(origin->position,delta);
  origin->fov=q.fov;origin->span=q.span;origin->nearPlane=q.nearPlane;origin->farPlane=q.farPlane;origin->orthographic=q.orthographic;
  if(a->flightKind==3)a->orbitTarget=nrAdd(a->orbitTarget,delta);
  for(int i=0;i<s->flight.count;i++)if(s->flight.steps[i].kind>=5)s->flight.steps[i].target=nrAdd(s->flight.steps[i].target,delta);
  s->flight.look=nrAdd(s->flight.look,nrV(q.yaw-before->yaw,q.pitch-before->pitch,q.roll-before->roll));
 }s->camera=q;a->grabActive=0;if(!a->enabled)memset(a,0,sizeof(*a));
}
static void defaults(OriginalCamera*a){memset(a,0,sizeof(*a));a->enabled=1;a->moveSpeed=12;a->turnSpeed=75;a->sensitivity=.32;}
static int numeric(const Json*j,int parent,const char*name,double*out,double lo,double hi){int t=nrField(j,parent,name);return t<0||(nrNumber(j,t,out)&&bounded(*out,lo,hi));}
static int vector(const Json*j,int parent,const char*name,Vec3*out,double limit){int t=nrField(j,parent,name);if(t<0)return 1;if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=3)return 0;double*a[3]={&out->x,&out->y,&out->z};for(int k=0,x=t+1;k<3;k++,x=j->tokens[x].next)if(!nrNumber(j,x,a[k])||!bounded(*a[k],-limit,limit))return 0;return 1;}
static int choice(const Json*j,int parent,const char*name,const char*const*names,int n,uint32_t*out){int t=nrField(j,parent,name);if(t<0)return 1;for(int k=0;k<n;k++)if(nrEqual(j,t,names[k])){*out=k;return 1;}return 0;}
static int boolean(const Json*j,int parent,const char*name,uint32_t*out){int t=nrField(j,parent,name),v;if(t<0)return 1;if(!nrBoolean(j,t,&v))return 0;*out=v;return 1;}
static void rotate(Camera*c,OriginalCamera*a,double yaw,double pitch){double distance=nrClamp(length(nrSub(c->position,a->target)),.2,1e300);c->yaw=wrap(c->yaw+yaw);c->pitch=nrClamp(c->pitch+pitch,-89,89);c->roll=wrap(c->roll);if(!a->navigation){Vec3 r,u,f;basis(c,&r,&u,&f);c->position=nrSub(a->target,nrScale(f,distance));}}
static void move(Camera*c,OriginalCamera*a,Vec3 local){Vec3 r,u,f;basis(c,&r,&u,&f);Vec3 next=nrAdd(c->position,nrAdd(nrAdd(nrScale(r,local.x),nrScale(u,local.y)),nrScale(f,local.z)));next.x=nrClamp(next.x,-100000,100000);next.y=nrClamp(next.y,-100000,100000);next.z=nrClamp(next.z,-100000,100000);a->target=nrAdd(a->target,nrSub(next,c->position));c->position=next;}
int nrOriginalCameraCommand(NrContext*c,State*s,const Json*j){
 if(s->schema<NR_STATE_SCHEMA_CAMERA_ORIGINAL)return reject(c,"Camera requires current schema");
 int op=nrField(j,0,"op"),profile=nrField(j,0,"profile");OriginalCamera*a=&s->originalCamera;Camera current=nrCameraCarrierAt(s);
 if(profile>=0&&!nrEqual(j,profile,"original")&&!nrEqual(j,profile,"default"))return reject(c,"Unknown camera profile");
 if(!a->enabled)defaults(a);
 if(nrEqual(j,op,"camera")){
  int original=profile<0||nrEqual(j,profile,"original");
  if(!nrAllowed(j,0,"op profile position yaw pitch roll near far fov span orthographic navigation target moveSpeed turnSpeed sensitivity"))return reject(c,"Unknown camera field");
  Camera q=current;uint32_t orthographic=q.orthographic;
  static const char*nav[]={"orbit","fly","pan"};
  if(!vector(j,0,"position",&q.position,original?100000:16000)||!numeric(j,0,"yaw",&q.yaw,-36000,36000)||!numeric(j,0,"pitch",&q.pitch,original?-89:-89.9,original?89:89.9)||!numeric(j,0,"roll",&q.roll,-36000,36000)||!numeric(j,0,"near",&q.nearPlane,.001,100)||!numeric(j,0,"far",&q.farPlane,original?1:.01,1000000)||!numeric(j,0,"fov",&q.fov,original?15:10,original?130:150)||!numeric(j,0,"span",&q.span,.1,2000)||!boolean(j,0,"orthographic",&orthographic)||!choice(j,0,"navigation",nav,3,&a->navigation)||!vector(j,0,"target",&a->target,100000)||!numeric(j,0,"moveSpeed",&a->moveSpeed,.1,1000)||!numeric(j,0,"turnSpeed",&a->turnSpeed,1,360)||!numeric(j,0,"sensitivity",&a->sensitivity,.01,5)||q.nearPlane>=q.farPlane)return reject(c,"Invalid camera");
  q.orthographic=orthographic;if(original){q.yaw=wrap(q.yaw);q.roll=wrap(q.roll);}else memset(a,0,sizeof(*a));nrCameraManualPose(s,&current,&q);return 0;
 }
 if(nrEqual(j,op,"camera-action")){
  if(!nrAllowed(j,0,"op action yaw pitch local units name points width height padding"))return reject(c,"Unknown camera action field");
  int action=nrField(j,0,"action");Camera q=current;
  if(nrEqual(j,action,"rotate")){double yaw=0,pitch=0;if(!numeric(j,0,"yaw",&yaw,-36000,36000)||!numeric(j,0,"pitch",&pitch,-36000,36000))return reject(c,"Invalid camera rotation");rotate(&q,a,yaw,pitch);}
  else if(nrEqual(j,action,"move")){Vec3 v={0};if(nrField(j,0,"local")<0||!vector(j,0,"local",&v,100000))return reject(c,"Invalid local movement");move(&q,a,v);}
  else if(nrEqual(j,action,"dolly")){double units=0;if(!numeric(j,0,"units",&units,-100000,100000))return reject(c,"Invalid dolly");if(a->navigation)move(&q,a,nrV(0,0,units));else{Vec3 r,u,f;basis(&q,&r,&u,&f);double d=nrClamp(length(nrSub(q.position,a->target))-units,.25,90000);q.position=nrSub(a->target,nrScale(f,d));}}
  else if(nrEqual(j,action,"view")){static const char*names[]={"front","back","left","right","top","bottom","iso"};const double angles[7][2]={{0,0},{180,0},{-90,0},{90,0},{0,-89},{0,89},{-28,-18}};uint32_t view=0;if(nrField(j,0,"name")<0||!choice(j,0,"name",names,7,&view))return reject(c,"Unknown camera view");uint32_t nav=a->navigation;a->navigation=0;rotate(&q,a,wrap(angles[view][0]-q.yaw),angles[view][1]-q.pitch);a->navigation=nav;}
  else if(nrEqual(j,action,"fit")){
   Vec3 points[NR_MAX_NODES*2];int count=0,token=nrField(j,0,"points"),vw,vh;nrSceneViewport(s,&vw,&vh);double width=vw,height=vh,padding=1.24;
   if(!numeric(j,0,"width",&width,1,10000)||!numeric(j,0,"height",&height,1,10000)||!numeric(j,0,"padding",&padding,1,10))return reject(c,"Invalid camera fit viewport");
   if(token>=0){if(j->tokens[token].type!=J_ARRAY||(unsigned)j->tokens[token].count>NR_MAX_NODES*2)return reject(c,"Invalid camera fit points");for(int t=token+1,k=0;k<j->tokens[token].count;k++,t=j->tokens[t].next){if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=3)return reject(c,"Invalid camera fit point");Vec3 v;double*coords[3]={&v.x,&v.y,&v.z};for(int a=0,x=t+1;a<3;a++,x=j->tokens[x].next)if(!nrNumber(j,x,coords[a])||!bounded(*coords[a],-100000,100000))return reject(c,"Invalid camera fit point");points[count++]=v;}}
   else for(unsigned i=0;i<NR_MAX_NODES;i++)if(s->nodes[i].used){Vec3 p=s->nodes[i].to;double w=5,h=3;if(s->sourceGraphLayout.enabled&&s->sourceGraphLayout.nodeIds[i]==(uint32_t)s->nodes[i].id){w=s->sourceGraphLayout.widths[i];h=s->sourceGraphLayout.heights[i];}points[count++]=nrAdd(p,nrV(-w,-h,0));points[count++]=nrAdd(p,nrV(w,h,0));}
   if(!count){q.position=nrV(0,0,40);q.yaw=q.pitch=q.roll=0;a->target=nrV(0,0,0);}
   else{Vec3 lo=points[0],hi=points[0];for(int i=1;i<count;i++){lo.x=nrClamp(lo.x,-1e300,points[i].x);lo.y=nrClamp(lo.y,-1e300,points[i].y);lo.z=nrClamp(lo.z,-1e300,points[i].z);hi.x=nrClamp(hi.x,points[i].x,1e300);hi.y=nrClamp(hi.y,points[i].y,1e300);hi.z=nrClamp(hi.z,points[i].z,1e300);}a->target=nrScale(nrAdd(lo,hi),.5);Vec3 right,up,forward;basis(&q,&right,&up,&forward);double horizontal=nrOriginalTan(q.fov*NR_PI/360),vertical=horizontal*height*2/width,distance=8;for(int i=0;i<count;i++){Vec3 d=nrSub(points[i],a->target);double z=nrDot(d,forward),x=nrAbs(nrDot(d,right))*padding/horizontal-z,y=nrAbs(nrDot(d,up))*padding/vertical-z;if(x>distance)distance=x;if(y>distance)distance=y;if(1-z>distance)distance=1-z;}q.position=nrSub(a->target,nrScale(forward,distance));}
  }
  else return reject(c,"Unknown camera action");
  if(!vectorBounded(q.position,100000))return reject(c,"Camera position range");nrCameraManualPose(s,&current,&q);return 0;
 }
 if(!nrEqual(j,op,"flight")||profile<0||!nrEqual(j,profile,"original")||!nrAllowed(j,0,"op profile steps cruise orbit"))return reject(c,"Unknown flight");
 int steps=nrField(j,0,"steps"),cruise=nrField(j,0,"cruise"),orbit=nrField(j,0,"orbit");if((steps>=0)+(cruise>=0)+(orbit>=0)!=1)return reject(c,"Choose one flight plan");
 memset(a->steps,0,sizeof(a->steps));a->stepCount=0;a->startUs=s->timeUs;a->origin=current;memset(&s->flight,0,sizeof(s->flight));
 if(steps>=0){
  if(j->tokens[steps].type!=J_ARRAY||j->tokens[steps].count<1||j->tokens[steps].count>64)return reject(c,"Flight supports 1..64 steps");
  a->flightKind=1;a->stepCount=j->tokens[steps].count;uint64_t total=0;Camera pose=current;static const char*kinds[]={"cruise","turn","climb","dive","roll"};
  for(uint32_t i=0,t=steps+1;i<a->stepCount;i++,t=j->tokens[t].next){OriginalFlightStep*m=&a->steps[i];m->bank=28;m->coordinated=1;double ms=1000,yaw=0,pitch=0,roll=0;
   if(!nrAllowed(j,t,"kind durationMs speed yaw pitch roll bank coordinated")||nrField(j,t,"kind")<0||!choice(j,t,"kind",kinds,5,&m->kind)||!numeric(j,t,"durationMs",&ms,10,600000)||!numeric(j,t,"speed",&m->speed,-100,100)||!numeric(j,t,"yaw",&yaw,-720,720)||!numeric(j,t,"pitch",&pitch,-720,720)||!numeric(j,t,"roll",&roll,-720,720)||!numeric(j,t,"bank",&m->bank,0,70)||!boolean(j,t,"coordinated",&m->coordinated))return reject(c,"Invalid manoeuvre");
   m->durationUs=(uint64_t)(ms*1000+.5);m->degrees=m->kind==1?yaw:m->kind==4?roll:pitch;total+=m->durationUs;if(total>3600000000ull)return reject(c,"Flight script exceeds one hour");pose=maneuver(pose,m,ms/1000);if(nrAbs(pose.pitch)>85)return reject(c,"Flight pitch outside -85..85");
  }
 }else if(cruise>=0){
  if(!nrAllowed(j,cruise,"speed heading")||!numeric(j,cruise,"speed",&a->speed,-100,100))return reject(c,"Invalid cruise");Camera travel=current;int heading=nrField(j,cruise,"heading");if(heading>=0&&(!nrAllowed(j,heading,"yaw pitch")||nrField(j,heading,"yaw")<0||nrField(j,heading,"pitch")<0||!numeric(j,heading,"yaw",&travel.yaw,-720,720)||!numeric(j,heading,"pitch",&travel.pitch,-89,89)))return reject(c,"Invalid cruise heading");Vec3 r,u;basis(&travel,&r,&u,&a->direction);a->flightKind=2;
 }else{
  static const char*modes[]={"stable","escape","falling"};a->periodSeconds=24;a->radialRate=1.2;a->bank=0;a->orbitMode=0;a->orbitTarget=nrV(0,0,0);
  if(!nrAllowed(j,orbit,"mode target periodSeconds radialRate bank")||!choice(j,orbit,"mode",modes,3,&a->orbitMode)||!vector(j,orbit,"target",&a->orbitTarget,100000)||!numeric(j,orbit,"periodSeconds",&a->periodSeconds,2,600)||!numeric(j,orbit,"radialRate",&a->radialRate,0,30)||!numeric(j,orbit,"bank",&a->bank,-70,70))return reject(c,"Invalid orbit");
  Vec3 d=nrSub(current.position,a->orbitTarget);a->radius=length(d);if(a->radius<.1)return reject(c,"Orbit target equals camera");a->radial=nrScale(d,1/a->radius);a->tangent=nrV(a->radial.z,0,-a->radial.x);double n=length(a->tangent);if(n<.01){a->tangent=nrV(1,0,0);n=1;}a->tangent=nrScale(a->tangent,1/n);a->flightKind=3;
 }
 return 0;
}
int nrValidOriginalCamera(const State*s){
 const OriginalCamera*a=&s->originalCamera;if(!a->enabled){
  OriginalCamera zero={0};if(s->schema<NR_STATE_SCHEMA_CAMERA_ANCHOR)return !memcmp(a,&zero,sizeof(zero));
  if(!a->grabActive)return !memcmp(a,&zero,sizeof(zero));
  if(a->grabActive!=1||a->grabSource>1||a->grabReserved||!nrValidViewport(a->grabWidth,a->grabHeight)||!vectorBounded(a->grabbed,1e9)||!s->pointerActive||s->pointerKind!=1)return 0;
  OriginalCamera rest=*a;rest.grabActive=rest.grabSource=rest.grabWidth=rest.grabHeight=0;rest.grabbed=nrV(0,0,0);return !memcmp(&rest,&zero,sizeof(zero));
 }
 if(a->enabled!=1||s->schema<NR_STATE_SCHEMA_CAMERA_ORIGINAL||a->navigation>2||a->flightKind>3||a->stepCount>64||a->startUs>s->timeUs||a->orbitMode>2||a->grabActive>1||a->grabSource>1||a->grabReserved||!vectorBounded(a->target,1e9)||!bounded(a->moveSpeed,.1,1000)||!bounded(a->turnSpeed,1,360)||!bounded(a->sensitivity,.01,5)||!vectorBounded(a->grabbed,1e9))return 0;
 if(a->grabActive&&(!nrValidViewport(a->grabWidth,a->grabHeight)))return 0;
 if(a->flightKind!=1&&a->stepCount)return 0;
 if(a->flightKind&&(!vectorBounded(a->origin.position,100000)||!bounded(a->origin.yaw,-1e9,1e9)||!bounded(a->origin.pitch,s->schema>=NR_STATE_SCHEMA_CAMERA_CONTROLS?-90:-89.9,s->schema>=NR_STATE_SCHEMA_CAMERA_CONTROLS?90:89.9)||!bounded(a->origin.roll,-1e9,1e9)||!bounded(a->origin.nearPlane,.001,100)||!bounded(a->origin.farPlane,.01,1000000)||a->origin.farPlane<=a->origin.nearPlane||!bounded(a->origin.fov,10,150)||!bounded(a->origin.span,.1,2000)||a->origin.orthographic<0||a->origin.orthographic>1))return 0;
 if(a->flightKind==1){if(!a->stepCount)return 0;uint64_t total=0;Camera pose=a->origin;for(uint32_t i=0;i<a->stepCount;i++){const OriginalFlightStep*m=&a->steps[i];if(m->kind>4||m->coordinated>1||m->durationUs<10000||m->durationUs>600000000||!bounded(m->speed,-100,100)||!bounded(m->degrees,-720,720)||!bounded(m->bank,0,70))return 0;total+=m->durationUs;pose=maneuver(pose,m,m->durationUs/1e6);if(nrAbs(pose.pitch)>85)return 0;}if(total>3600000000ull)return 0;}
 if(a->flightKind==2&&(!bounded(a->speed,-100,100)||!vectorBounded(a->direction,1.0000001)))return 0;
 if(a->flightKind==3&&(!vectorBounded(a->orbitTarget,100000)||!vectorBounded(a->radial,1.0000001)||!vectorBounded(a->tangent,1.0000001)||!bounded(a->radius,.1,1e12)||!bounded(a->periodSeconds,2,600)||!bounded(a->radialRate,0,30)||!bounded(a->bank,-70,70)))return 0;
 return 1;
}
/* The retained grab record is shared by both camera profiles. Epoch88 adds
 * only the default-profile active grab; all other disabled fields stay zero. */
static void gestureBasis(const State*s,const Camera*c,Vec3*r,Vec3*u,Vec3*f){if(s->originalCamera.enabled)basis(c,r,u,f);else nrBasis(c,r,u,f);}
static Vec3 pointerOffset(const State*s,const Camera*camera,double x,double y,int orthographic){
 const OriginalCamera*a=&s->originalCamera;Vec3 r,u,f;gestureBasis(s,camera,&r,&u,&f);
 double width=a->grabWidth?a->grabWidth:s->width,height=a->grabHeight?a->grabHeight:s->height;
 double focal=a->grabSource?width*cosine(camera->fov*NR_PI/360)/(2*sine(camera->fov*NR_PI/360)):height*cosine(camera->fov*NR_PI/360)/sine(camera->fov*NR_PI/360);
 if(!a->enabled&&!a->grabSource)focal=height*nrCos(camera->fov*.5)/nrSin(camera->fov*.5);
 double divisor=orthographic?width/camera->span:focal;
 return nrAdd(nrScale(r,(x-width/2)/divisor),nrScale(u,-(y-height/2)*2/divisor));
}
/* Invert the source raster's actual quantized transform. Its table coefficients
 * are not perfectly orthonormal, so an analytic camera basis is not its inverse. */
static void pickCoverage(void*u,int32_t x,int32_t y,int32_t d,uint32_t rgb,int32_t a,int32_t t){(void)u;(void)x;(void)y;(void)d;(void)rgb;(void)a;(void)t;}
static int sourcePickPoint(const State*s,int width,int height,double x,double y,double depth,Vec3*out){
 NrScenicArtConfig q;NrScenicSourceRaster r;
 int valid=s->sceneArt.used?nrSceneArtEffective(s,width,height,&q):s->sourceModel.view.used?nrSourceModelEffective(s,width,height,&q):0;
 if(!valid||!nrScenicSourceRasterInit(&r,&q,width,height,pickCoverage,0))return 0;
 double px=(x/width-.5)*r.sampleWidth*16,py=(.5-y/height)*r.sampleHeight*16,d=depth*256;
 if(r.orthographic){px*=q.world[NR_WORLD_SPAN]/(double)(r.sampleWidth*16);py*=q.world[NR_WORLD_SPAN]/(double)(r.sampleWidth*16);}
 else{px*=d/r.focal;py*=d/r.focal;}
 double cr=r.cosRoll,sr=r.sinRoll,cp=r.cosPitch,sp=r.sinPitch,cy=r.cosYaw,sy=r.sinYaw;
 double a=(px*cr-py*sr)*1000/(cr*cr+sr*sr),u=(py*cr+px*sr)*1000/(cr*cr+sr*sr);
 double wy=(u*cp+d*sp)*1000/(cp*cp+sp*sp),b=(d*cp-u*sp)*1000/(cp*cp+sp*sp);
 double wx=(a*cy+b*sy)*1000/(cy*cy+sy*sy),wz=(b*cy-a*sy)*1000/(cy*cy+sy*sy);
 *out=nrV((q.world[NR_WORLD_CAMERA_X]+wx)/256,(q.world[NR_WORLD_CAMERA_Y]+wy)/256,-(q.world[NR_WORLD_CAMERA_Z]+wz)/256);return 1;
}
void nrOriginalCameraGrab(NrContext*c,State*s,double x,double y){
 OriginalCamera*a=&s->originalCamera;if(!a->enabled)memset(a,0,sizeof(*a));a->grabActive=0;if(nrCameraPathOwned(s)||(!s->cameraControls.configured&&(a->navigation||a->flightKind||s->flight.count)))return;
 Camera camera=nrCameraAt(s);Vec3 r,u,f;gestureBasis(s,&camera,&r,&u,&f);
 double depth=nrDot(nrSub(a->target,camera.position),f);if(depth<camera.nearPlane)depth=length(nrSub(a->target,camera.position));if(depth<camera.nearPlane)depth=40;
 int sourceRaster=c->sourceActive&&c->sourcePickDepth,pickedSource=0,windowPerspective=s->windowApplication.enabled;
 a->grabSource=s->windowApplication.enabled||sourceRaster;if(a->enabled)for(unsigned i=0;i<NR_MAX_NODES;i++)if(s->nodes[i].used){a->grabSource=1;break;}a->grabWidth=s->width;a->grabHeight=s->height;
 if(sourceRaster){a->grabWidth=c->sourceWidth;a->grabHeight=c->sourceHeight;}
 else if(!s->windowApplication.enabled){int width,height;nrSceneViewport(s,&width,&height);a->grabWidth=width;a->grabHeight=height;}
 size_t cell=(size_t)(int)y*s->width+(int)x;uint32_t family=c->cells[cell].id&0xff000000u;
 if(family==NR_ID_WINDOW&&c->windowDepth&&bounded(c->windowDepth[cell],camera.nearPlane,camera.farPlane)){depth=c->windowDepth[cell];a->grabSource=1;windowPerspective=1;}
 else if(family==NR_ID_NODE){int slot=nrFindNode(s,(int)(c->cells[cell].id&0xffff));if(slot>=0){double d=nrDot(nrSub(nrNodeAt(&s->nodes[slot],s->timeUs),camera.position),f);if(bounded(d,camera.nearPlane,camera.farPlane))depth=d;}}
 else if(c->screenWidth>0&&c->screenHeight>0){
  double nearest=1e300;
  for(int yy=0;yy<4;yy++){for(int xx=0;xx<2;xx++){int px=(int)x*2+xx,py=(int)y*4+yy;if(px>=c->screenWidth||py>=c->screenHeight)continue;size_t index=(size_t)py*c->screenWidth+px;
   if(c->fragmentCounts[index]){double d=c->fragments[index][0].depth/1024.0;if(d>0&&d<nearest){nearest=d;pickedSource=0;}}
   if(sourceRaster&&c->sourcePickDepth[index]>0){
    int32_t encoded=c->sourcePickDepth[index];
    double d=c->sourceOrthographic?(268435456.0-encoded)/256.0:67108864.0/(256.0*encoded);
    if(d>0&&d<nearest){nearest=d;pickedSource=1;}
   }
  }}
  if(nearest<1e300)depth=nearest;
 }
 /* Source windows use the perspective-only nrWindowSourceProject. Graph cards,
  * fragments and empty background use nrProjection, which honours orthographic;
  * grabSource there selects only the original horizontal field of view. */
 int orthographic=sourceRaster?c->sourceOrthographic:camera.orthographic&&!windowPerspective;
 Vec3 offset=pointerOffset(s,&camera,x,y,orthographic);
 a->grabbed=nrAdd(camera.position,orthographic?nrAdd(offset,nrScale(f,depth)):nrScale(nrAdd(f,offset),depth));
 if(pickedSource)sourcePickPoint(s,a->grabWidth,a->grabHeight,x,y,depth,&a->grabbed);
 if(s->cameraControls.configured&&s->cameraControls.anchorEnabled)a->grabbed=s->cameraControls.anchor;if(a->enabled)a->target=a->grabbed;a->grabActive=1;
}
void nrOriginalCameraDrag(State*s,double dx,double dy,int pan){
 if(s->cameraControls.configured){nrCameraControlInput(s,dx,dy,0,pan);return;}
 OriginalCamera*a=&s->originalCamera;Camera camera=nrCameraCarrierAt(s);
 if(pan||a->navigation==2){if(nrCameraPathOwned(s))return;Camera before=camera;move(&camera,a,nrV(-dx*.5,dy*.6,0));nrCameraManualPose(s,&before,&camera);return;}
 double rate=a->enabled?a->sensitivity*2:.65,yaw=dx*rate,pitch=-dy*rate;
 if((a->flightKind||s->flight.count)&&!nrCameraPathOwned(s)){s->flight.look.x+=yaw;s->flight.look.y=nrClamp(s->flight.look.y+pitch,-85,85);return;}
 if(!a->navigation&&a->grabActive)nrCameraRotatePose(&camera,a->grabbed,nrV(pitch,-yaw,0),1,1);
 else {camera.yaw=wrap(camera.yaw+yaw);camera.pitch=nrClamp(camera.pitch+pitch,-89,89);}
 s->camera=camera;
}
