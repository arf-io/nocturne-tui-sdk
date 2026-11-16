#include "internal.h"
/* Binary64 analytic height field; no authored state or hidden clock. */
static int finiteWave(double value) {
    uint64_t bits;memcpy(&bits,&value,8);
    return (bits&0x7ff0000000000000ull)!=0x7ff0000000000000ull;
}
static void waveTrig(double phase,double *sine,double *cosine) {
    phase-=nrFloor((phase+NR_PI)/(2*NR_PI))*2*NR_PI;
    double term=phase,s=phase,c=1,ct=1,p2=phase*phase;
    for(int k=1;k<=16;k++) {
        term*=-p2/((2.0*k)*(2.0*k+1));s+=term;
        ct*=-p2/((2.0*k-1)*(2.0*k));c+=ct;
    }
    *sine=s;*cosine=c;
}
int nrWaveSample(const double *waves,uint32_t count,double x,double z,double seconds,double *out,uint32_t capacity) {
    if(count>32||(!waves&&count)||!out||capacity<6||
       ((uintptr_t)waves%8)||((uintptr_t)out%8)||!finiteWave(x)||!finiteWave(z)||!finiteWave(seconds))return -1;
    if(x<-1000000||x>1000000||z<-1000000||z>1000000||seconds<-1000000||seconds>1000000)return -1;
    double h=0,dx=0,dz=0,velocity=0,laplacian=0;
    for(uint32_t i=0;i<count;i++) {
        const double *w=waves+i*5;
        for(int k=0;k<5;k++)if(!finiteWave(w[k])||w[k]<-1000000||w[k]>1000000)return -1;
        double a=w[0],kx=w[1],kz=w[2],omega=w[3],s,c;
        waveTrig(kx*x+kz*z-omega*seconds+w[4],&s,&c);
        h+=a*c;dx-=a*kx*s;dz-=a*kz*s;velocity+=a*omega*s;
        laplacian-=a*(kx*kx+kz*kz)*c;
    }
    double length=nrSqrt(1+dx*dx+dz*dz);
    double result[6]={h,-dx/length,1/length,-dz/length,velocity,laplacian};
    for(int i=0;i<6;i++)if(!finiteWave(result[i]))return -1;
    memcpy(out,result,sizeof(result));return 1;
}

int nrSurfaceWavesCommand(NrContext*c,State*s,const Json*j) {
    memcpy(c->error,"Invalid surface wave configuration",35);
    if(!nrAllowed(j,0,"op surfaceId waves"))return -1;
    int idToken=nrField(j,0,"surfaceId"),wavesToken=nrField(j,0,"waves");double id;
    if(idToken<0||!nrNumber(j,idToken,&id)||id<1||id>NR_SURFACES||id!=(int)id||
       !s->geometry.surfaces[(int)id-1].used||wavesToken<0||j->tokens[wavesToken].type!=J_ARRAY||j->tokens[wavesToken].count>32)return -1;
    int slot=(int)id-1,token=wavesToken+1,count=j->tokens[wavesToken].count;
    double waves[32][5]={{0}},amplitude=0;
    for(int i=0;i<count;i++) {
        if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count!=5)return -1;
        int value=token+1;
        for(int k=0;k<5;k++){if(!nrNumber(j,value,&waves[i][k]))return -1;value=j->tokens[value].next;}
        amplitude+=nrAbs(waves[i][0]);token=j->tokens[token].next;
    }
    double output[6];if(amplitude>256||nrWaveSample(&waves[0][0],count,0,0,0,output,6)!=1)return -1;
    memset(&s->surfaceWaves[slot],0,sizeof(s->surfaceWaves[slot]));
    s->surfaceWaves[slot].count=count;memcpy(s->surfaceWaves[slot].waves,waves,sizeof(waves));
    return nrBuildGeometry(s,&s->geometry.index)?0:-1;
}
int nrValidSurfaceWaves(const State*s) {
    for(int slot=0;slot<NR_SURFACES;slot++) {
        uint32_t count=s->surfaceWaves[slot].count;double out[6],amplitude=0;
        if(count>32||s->surfaceWaves[slot].padding||(count&&!s->geometry.surfaces[slot].used))return 0;
        for(uint32_t i=0;i<count;i++)amplitude+=nrAbs(s->surfaceWaves[slot].waves[i][0]);
        if(amplitude>256||nrWaveSample(&s->surfaceWaves[slot].waves[0][0],count,0,0,0,out,6)!=1)return 0;
    }
    return 1;
}
void nrDisplaceSurfaceTriangle(const State*s,int index,Triangle*out) {
    nrFlowThicknessTriangleAt(s,index,s->timeUs,out);
    int id=s->geometry.triangleSurfaces[index];if(id<=0)return;
    Vec3*points[3]={&out->a,&out->b,&out->c};double result[6];
    if(s->surfaceWaves[id-1].count)for(int i=0;i<3;i++)if(nrWaveSample(&s->surfaceWaves[id-1].waves[0][0],s->surfaceWaves[id-1].count,points[i]->x,points[i]->z,s->timeUs/1000000.0,result,6)==1)points[i]->y+=result[0];
    if(s->surfaceFluids[id-1].used)for(int i=0;i<3;i++){
        const SurfaceFluidPose*pose=&s->surfacePoses[id-1];
        if(pose->used&&nrSurfacePoseMotion(pose->orientation,pose->pivot,s->surfaceFluids[id-1].offset,nrV(0,0,0),nrV(0,0,0),*points[i],result))
            *points[i]=nrV(result[0],result[1],result[2]);
        else *points[i]=nrAdd(*points[i],s->surfaceFluids[id-1].offset);
    }
}

int nrSurfaceWaveSample(const NrContext*c,uint32_t id,double x,double z,double*out,uint32_t capacity) {
    if(!c||c->state.magic!=NR_MAGIC||id<1||id>NR_SURFACES||!c->state.geometry.surfaces[id-1].used||!nrExternalOutput(c,out,6*sizeof(double)))return -1;
    if(!out||capacity<6||((uintptr_t)out%8))return -1;
    if(!finiteWave(x)||!finiteWave(z)||x<-1000000||x>1000000||z<-1000000||z>1000000)return -1;
    if(c->state.surfacePoses[id-1].used){
        /* A rotated surface is not generally a single analytic height field.
         * Sample the topmost projected rendered facet, retaining source order
         * for equal heights. Vertical facets have no unique XZ height. */
        double row[6];if(!nrWaterHeight(&c->state,(int)id,x,z,row))return -1;
        row[5]=0;memcpy(out,row,sizeof(row));return 1;
    }
    const SurfaceFluid*f=&c->state.surfaceFluids[id-1];double row[6];
    int result=nrWaveSample(&c->state.surfaceWaves[id-1].waves[0][0],c->state.surfaceWaves[id-1].count,x-f->offset.x,z-f->offset.z,c->state.timeUs/1000000.0,row,6);
    if(result!=1)return result;if(f->used){row[0]+=f->offset.y;if(f->used==1)row[4]+=f->velocity.y;}memcpy(out,row,sizeof(row));return 1;
}

static Vec3 surfaceLocalPoint(const State*s,int id,Vec3 point){
    const SurfaceFluid*f=&s->surfaceFluids[id-1];const SurfaceFluidPose*pose=&s->surfacePoses[id-1];double row[6];
    if(pose->used&&nrSurfacePoseInverse(pose->orientation,pose->pivot,f->offset,nrV(0,0,0),nrV(0,0,0),point,nrV(0,0,0),row))return nrV(row[0],row[1],row[2]);
    return nrSub(point,f->offset);
}
static Vec3 surfaceWorldVelocity(const State*s,int id,Vec3 point,Vec3 localVelocity){
    const SurfaceFluid*f=&s->surfaceFluids[id-1];const SurfaceFluidPose*pose=&s->surfacePoses[id-1];
    Vec3 translation=f->used==1?f->velocity:nrV(0,0,0);
    if(!pose->used)return nrAdd(translation,localVelocity);
    Vec3 quaternion=nrV(pose->orientation[0],pose->orientation[1],pose->orientation[2]);
    Vec3 t=nrScale(nrCross(quaternion,localVelocity),2);
    Vec3 rotated=nrAdd(localVelocity,nrAdd(nrScale(t,pose->orientation[3]),nrCross(quaternion,t)));
    Vec3 angular=f->used==1?s->angularFluids[id-1].omega:nrV(0,0,0);
    Vec3 radius=nrSub(point,nrAdd(pose->pivot,f->offset));
    return nrAdd(nrAdd(translation,nrCross(angular,radius)),rotated);
}
Vec3 nrSurfaceTriangleVelocity(const State*s,int index,Vec3 point) {
    int id=s->geometry.triangleSurfaces[index];if(id<=0)return nrV(0,0,0);
    if(s->flowThicknessTriangles[index].role)return surfaceWorldVelocity(s,id,point,nrFlowThicknessVelocity(s,index,surfaceLocalPoint(s,id,point)));
    if(!s->surfaceWaves[id-1].count)return surfaceWorldVelocity(s,id,point,nrV(0,0,0));
    Triangle triangle=s->mesh[index];nrDisplaceSurfaceTriangle(s,index,&triangle);
    Vec3 ab=nrSub(triangle.b,triangle.a),ac=nrSub(triangle.c,triangle.a),ap=nrSub(point,triangle.a);
    double aa=nrDot(ab,ab),bb=nrDot(ac,ac),cross=nrDot(ab,ac),denominator=aa*bb-cross*cross;
    if(denominator<=0)return surfaceWorldVelocity(s,id,point,nrV(0,0,0));
    double u=(nrDot(ap,ab)*bb-nrDot(ap,ac)*cross)/denominator;
    double v=(nrDot(ap,ac)*aa-nrDot(ap,ab)*cross)/denominator;
    Vec3 points[3]={surfaceLocalPoint(s,id,triangle.a),surfaceLocalPoint(s,id,triangle.b),surfaceLocalPoint(s,id,triangle.c)};double weights[3]={1-u-v,u,v},velocity=0,result[6];
    for(int i=0;i<3;i++)if(nrWaveSample(&s->surfaceWaves[id-1].waves[0][0],s->surfaceWaves[id-1].count,points[i].x,points[i].z,s->timeUs/1000000.0,result,6)==1)velocity+=weights[i]*result[4];
    return surfaceWorldVelocity(s,id,point,nrV(0,velocity,0));
}

typedef struct {
    const State *state;
    int index,id;
    Triangle base;
    Vec3 from,delta;
    double start,duration,weights[3],rates[3];
} WaveSweep;
static double sweepGap(const WaveSweep*q,double fraction,double*derivative,Triangle*shape,Vec3*surfaceVelocity) {
    Vec3 base[3]={q->base.a,q->base.b,q->base.c},points[3];
    double y=0,dy=0,velocity=0,seconds=q->start+fraction*q->duration,result[6];
    for(int k=0;k<3;k++) {
        nrWaveSample(&q->state->surfaceWaves[q->id-1].waves[0][0],q->state->surfaceWaves[q->id-1].count,base[k].x,base[k].z,seconds,result,6);
        double weight=q->weights[k]+q->rates[k]*fraction;
        points[k]=base[k];points[k].y+=result[0];
        y+=weight*points[k].y;
        dy+=q->rates[k]*points[k].y+weight*q->duration*result[4];
        velocity+=weight*result[4];
    }
    if(derivative)*derivative=q->delta.y-dy;
    if(shape){*shape=q->base;shape->a=points[0];shape->b=points[1];shape->c=points[2];}
    if(surfaceVelocity)*surfaceVelocity=nrV(0,velocity,0);
    return q->from.y+fraction*q->delta.y-y;
}
/* Left-first interval subdivision uses a conservative gap derivative bound.
 * It cannot certify a miss from endpoint samples alone. Exhaustion rejects the
 * enclosing native time transaction instead of silently dropping a contact. */
int nrWaveTriangleHit(const State*s,int index,Vec3 from,Vec3 to,double start,double duration,double maximum,GeometryHit*out) {
    Triangle base=s->mesh[index];Vec3 ab=nrSub(base.b,base.a),ac=nrSub(base.c,base.a),ap=nrSub(from,base.a),delta=nrSub(to,from);
    double determinant=ab.x*ac.z-ab.z*ac.x;
    if(determinant==0) {
        Vec3 normal=nrNormal(nrCross(ab,ac));double direction=nrDot(normal,delta);
        if(direction==0)return 0;
        double at=-nrDot(normal,ap)/direction;if(at<0||at>maximum)return 0;
        Vec3 points[3]={base.a,base.b,base.c};double velocities[3],sample[6];
        int id=s->geometry.triangleSurfaces[index];
        for(int k=0;k<3;k++) {
            nrWaveSample(&s->surfaceWaves[id-1].waves[0][0],s->surfaceWaves[id-1].count,points[k].x,points[k].z,start+at*duration,sample,6);
            points[k].y+=sample[0];velocities[k]=sample[4];
        }
        Vec3 point=nrAdd(from,nrScale(delta,at)),e1=nrSub(points[1],points[0]),e2=nrSub(points[2],points[0]),offset=nrSub(point,points[0]);
        double aa=nrDot(e1,e1),bb=nrDot(e2,e2),cross=nrDot(e1,e2),denom=aa*bb-cross*cross;
        if(denom<=0)return 0;
        double u=(nrDot(offset,e1)*bb-nrDot(offset,e2)*cross)/denom,v=(nrDot(offset,e2)*aa-nrDot(offset,e1)*cross)/denom;
        if(u<0||v<0||u+v>1)return 0;
        if(direction>0)normal=nrScale(normal,-1);
        memset(out,0,sizeof(*out));out->fraction=at;out->position=point;out->normal=normal;
        out->surfaceVelocity=nrV(0,(1-u-v)*velocities[0]+u*velocities[1]+v*velocities[2],0);
        out->triangleIndex=index;out->surfaceId=id;return 1;
    }
    WaveSweep q={.state=s,.index=index,.id=s->geometry.triangleSurfaces[index],.base=base,.from=from,.delta=delta,.start=start,.duration=duration};
    q.weights[1]=(ap.x*ac.z-ap.z*ac.x)/determinant;
    q.weights[2]=(ab.x*ap.z-ab.z*ap.x)/determinant;
    q.weights[0]=1-q.weights[1]-q.weights[2];
    q.rates[1]=(delta.x*ac.z-delta.z*ac.x)/determinant;
    q.rates[2]=(ab.x*delta.z-ab.z*delta.x)/determinant;
    q.rates[0]=-q.rates[1]-q.rates[2];
    double low=0,high=maximum;
    for(int k=0;k<3;k++) {
        if(q.rates[k]==0){if(q.weights[k]<-1e-10)return 0;}
        else {double edge=-q.weights[k]/q.rates[k];if(q.rates[k]>0){if(edge>low)low=edge;}else if(edge<high)high=edge;}
    }
    if(low>high||high<0||low>maximum)return 0;
    if(low<0)low=0;if(high>maximum)high=maximum;
    double amplitude=0,speed=0,acceleration=0;
    for(uint32_t i=0;i<s->surfaceWaves[q.id-1].count;i++) {
        const double*w=s->surfaceWaves[q.id-1].waves[i];amplitude+=nrAbs(w[0]);speed+=nrAbs(w[0]*w[3]);acceleration+=nrAbs(w[0]*w[3]*w[3]);
    }
    double limit=nrAbs(delta.y-q.rates[0]*base.a.y-q.rates[1]*base.b.y-q.rates[2]*base.c.y)+
        amplitude*(nrAbs(q.rates[0])+nrAbs(q.rates[1])+nrAbs(q.rates[2]))+duration*speed;
    if(limit<1e-14)return 0;
    double secondLimit=2*duration*speed*(nrAbs(q.rates[0])+nrAbs(q.rates[1])+nrAbs(q.rates[2]))+duration*duration*acceleration;
    struct {double low,high,leftGap,rightGap;} stack[64];int size=1,work=0;
    stack[0].low=low;stack[0].high=high;stack[0].leftGap=sweepGap(&q,low,0,0,0);stack[0].rightGap=sweepGap(&q,high,0,0,0);
    while(size) {
        if(++work>4096)return -1;
        --size;double a=stack[size].low,b=stack[size].high,ga=stack[size].leftGap,gb=stack[size].rightGap,mid=(a+b)*.5;
        double error=secondLimit*(b-a)*(b-a)/8+1e-12;
        if((ga>error&&gb>error)||(ga< -error&&gb< -error))continue;
        double gap=sweepGap(&q,mid,0,0,0);
        if(nrAbs(gap)>limit*(b-a)*.5+1e-12)continue;
        if(b-a<=1e-10) {
            if(mid<=1e-10||(ga>0&&gb>0)||(ga<0&&gb<0))continue;
            double derivative;Triangle triangle;Vec3 velocity;
            sweepGap(&q,mid,&derivative,&triangle,&velocity);
            if(nrAbs(derivative)<1e-12)continue;
            Vec3 normal=nrNormal(nrCross(nrSub(triangle.b,triangle.a),nrSub(triangle.c,triangle.a)));
            Vec3 relative=nrSub(nrScale(delta,1/duration),velocity);
            if(nrDot(normal,relative)>0)normal=nrScale(normal,-1);
            memset(out,0,sizeof(*out));out->fraction=mid;out->position=nrAdd(from,nrScale(delta,mid));
            out->normal=normal;out->surfaceVelocity=velocity;out->triangleIndex=index;out->surfaceId=q.id;return 1;
        }
        if(size+2>64)return -1;
        stack[size].low=mid;stack[size].high=b;stack[size].leftGap=gap;stack[size++].rightGap=gb;
        stack[size].low=a;stack[size].high=mid;stack[size].leftGap=ga;stack[size++].rightGap=gap;
    }
    return 0;
}

int nrWaveBindingNumberValid(const Value*v,double value){
    if(v->bindingFamily!=17||!nrResourceBindingShapeValid(v)||!finiteWave(value)||value< -1000000||value>1000000)return 0;
    const char*member=strrchr(v->field,'.');
    return strcmp(member+1,"amplitude")!=0||(value>=-256&&value<=256);
}

int nrBindWaveValue(State*s,const Value*v,double value){
    if(v->bindingId<1||v->bindingId>NR_SURFACES||!s->geometry.surfaces[v->bindingId-1].used||
       !nrWaveBindingNumberValid(v,value))return 0;
    const char*p=v->field+6;int index=0;
    if(*p<'0'||*p>'9'||(*p=='0'&&p[1]!='.'))return 0;
    while(*p>='0'&&*p<='9'){index=index*10+(*p++-'0');if(index>=32)return 0;}
    if(*p++!='.')return 0;
    const char*members[]={"amplitude","kx","kz","omega","phase"};int member=-1;
    for(int i=0;i<5;i++)if(!strcmp(p,members[i]))member=i;
    int slot=v->bindingId-1;if(member<0||index>=(int)s->surfaceWaves[slot].count)return 0;
    double before=s->surfaceWaves[slot].waves[index][member];
    s->surfaceWaves[slot].waves[index][member]=value;
    if(!nrValidSurfaceWaves(s)||!nrBuildGeometry(s,&s->geometry.index)){
        s->surfaceWaves[slot].waves[index][member]=before;return 0;
    }return 1;
}
