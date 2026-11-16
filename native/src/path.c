#include "internal.h"
/* Piecewise-linear arc length in the same world coordinates as ribbon points. */
int nrPathSample(const double*points,uint32_t count,int closed,int mode,double distance,double*out,uint32_t capacity) {
    if(!points||((uintptr_t)points&7)||!out||((uintptr_t)out&7)||capacity<8||closed<0||closed>1||mode<0||mode>2||count<(closed?3u:2u)||count>(closed?128u:129u)||!(distance>=-1e12&&distance<=1e12))return -1;
    Vec3 p[129];double lengths[128],total=0;uint32_t segments=count-1+closed;
    for(uint32_t i=0;i<count;i++){
        for(int k=0;k<3;k++)if(!(points[i*3+k]>=-16000&&points[i*3+k]<=16000))return -1;
        p[i]=nrV(points[i*3],points[i*3+1],points[i*3+2]);
    }
    for(uint32_t i=0;i<segments;i++){Vec3 delta=nrSub(p[(i+1)%count],p[i]);lengths[i]=nrSqrt(nrDot(delta,delta));if(lengths[i]<1e-8)return -1;total+=lengths[i];}
    double at=distance,direction=1;
    if(mode==0){if(at<0)at=0;if(at>total)at=total;}
    else {
        double period=total*(mode==2?2:1),remainder=nrAbs(at),chunk=period;
        /* Binary reduction avoids overflowing integer conversion for tiny paths. */
        while(chunk<=remainder*.5)chunk*=2;
        while(chunk>=period){if(remainder>=chunk)remainder-=chunk;chunk*=.5;}
        at=distance<0&&remainder>0?period-remainder:remainder;
        if(at>=period)at=0;
        if(mode==2&&at>=total){at=period-at;direction=-1;}
    }
    uint32_t segment=0;double local=at;
    while(segment+1<segments&&local>=lengths[segment]){local-=lengths[segment];segment++;}
    Vec3 delta=nrSub(p[(segment+1)%count],p[segment]),position=nrAdd(p[segment],nrScale(delta,local/lengths[segment])),tangent=nrScale(delta,direction/lengths[segment]);
    double result[8]={position.x,position.y,position.z,tangent.x,tangent.y,tangent.z,total,at};memcpy(out,result,sizeof(result));return 1;
}

static int pathReject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int pathNumber(const Json*j,int object,const char*key,double*out,double low,double high){int t=nrField(j,object,key);if(t<0)return 1;double v;if(!nrNumber(j,t,&v)||!(v>=low&&v<=high))return 0;*out=v;return 1;}
static int pathId(const Json*j,int object,const char*key,uint32_t*out,int minimum){double v=*out;if(!pathNumber(j,object,key,&v,minimum,65535)||v!=(uint32_t)v)return 0;*out=v;return 1;}
static Vec3* pathTarget(State*s,int actor){
    int family=s->pathActors[actor].family;uint32_t id=s->pathActors[actor].targetId;
    if(!family)return &s->camera.position;
    if(family==1){for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(s->emitters[i].used&&s->emitters[i].id==id&&s->emitters[i].generation==s->pathActors[actor].generation)return &s->emitters[i].position;}
    if(family==2){for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windows[i].used&&s->windows[i].id==(int)id)return &s->windows[i].position;}
    if(family==3){for(int i=0;i<(int)NR_MAX_NODES;i++)if(s->nodes[i].used&&s->nodes[i].id==(int)id)return &s->nodes[i].position;}
    return 0;
}
int nrPathActorsTick(State*s){
    for(int i=0;i<16;i++)if(s->pathActors[i].used){
        Vec3*position=pathTarget(s,i);if(!position)continue;
        double elapsed=s->timeUs>=s->pathActors[i].startUs?(s->timeUs-s->pathActors[i].startUs)/1000000.0:0,out[8];
        if(nrPathSample(&s->pathActors[i].points[0][0],s->pathActors[i].count,s->pathActors[i].closed,s->pathActors[i].mode,s->pathActors[i].distance+s->pathActors[i].speed*elapsed,out,8)!=1)return 0;
        /* Target families have narrower authoring bounds than mesh coordinates. */
        double bound=16000;
        if(nrAbs(out[0])>bound||nrAbs(out[1])>bound||nrAbs(out[2])>bound)return 0;
        *position=nrV(out[0],out[1],out[2]);
        if(s->pathActors[i].family==3)for(int k=0;k<(int)NR_MAX_NODES;k++)if(s->nodes[k].used&&s->nodes[k].id==(int)s->pathActors[i].targetId){s->nodes[k].from=s->nodes[k].to=*position;s->nodes[k].durationUs=0;}
    }return 1;
}
int nrValidPathActors(const State*s){
    for(int i=0;i<16;i++)if(s->pathActors[i].used){
        if(s->pathActors[i].used!=1||!s->pathActors[i].id||s->pathActors[i].id>65535||s->pathActors[i].family<0||s->pathActors[i].family>3||s->pathActors[i].targetId>65535||(!s->pathActors[i].family&&s->pathActors[i].targetId)|| (s->pathActors[i].family&&!s->pathActors[i].targetId)||s->pathActors[i].startUs>s->timeUs||(s->pathActors[i].family==1&&(!s->pathActors[i].generation||s->pathActors[i].generation>s->nextEmitterGeneration))||(s->pathActors[i].family!=1&&s->pathActors[i].generation)||!(s->pathActors[i].speed>=-10000&&s->pathActors[i].speed<=10000))return 0;
        double out[8];if(nrPathSample(&s->pathActors[i].points[0][0],s->pathActors[i].count,s->pathActors[i].closed,s->pathActors[i].mode,s->pathActors[i].distance,out,8)!=1)return 0;
        for(int k=0;k<i;k++)if(s->pathActors[k].used&&(s->pathActors[k].id==s->pathActors[i].id||(s->pathActors[k].family==s->pathActors[i].family&&s->pathActors[k].targetId==s->pathActors[i].targetId)))return 0;
    }else if(s->pathActors[i].used)return 0;
    return 1;
}
int nrPathTravelCommand(NrContext*c,State*s,const Json*j){
    uint32_t id=0;if(nrField(j,0,"id")<0||!pathId(j,0,"id",&id,1))return pathReject(c,"Path actor id required");int slot=-1,freeSlot=-1;
    for(int i=0;i<16;i++){if(s->pathActors[i].used&&s->pathActors[i].id==id)slot=i;if(!s->pathActors[i].used&&freeSlot<0)freeSlot=i;}
    if(nrEqual(j,nrField(j,0,"op"),"remove-path-travel")){if(!nrAllowed(j,0,"op id"))return pathReject(c,"Unknown path removal field");if(slot>=0){if(!s->pathActors[slot].family){s->flight.count=0;nrOriginalCameraStop(s);}memset(&s->pathActors[slot],0,sizeof(s->pathActors[slot]));}return 0;}
    if(!nrAllowed(j,0,"op id target points speed distance mode closed"))return pathReject(c,"Unknown path travel field");
    if(slot<0)slot=freeSlot;if(slot<0)return pathReject(c,"Path actor capacity");
    int target=nrField(j,0,"target"),points=nrField(j,0,"points"),family=-1;
    if(target<0||j->tokens[target].type!=J_OBJECT||!nrAllowed(j,target,"family id"))return pathReject(c,"Path target required");
    const char*names[]={"camera","emitter","window","node"};for(int k=0;k<4;k++)if(nrEqual(j,nrField(j,target,"family"),names[k]))family=k;
    uint32_t targetId=0;if(family<0||nrField(j,target,"id")<0||!pathId(j,target,"id",&targetId,family?1:0)||(!family&&targetId))return pathReject(c,"Invalid path target");
    for(int i=0;i<16;i++)if(i!=slot&&s->pathActors[i].used&&s->pathActors[i].family==family&&s->pathActors[i].targetId==targetId)return pathReject(c,"Path target already owned");
    if(points<0||j->tokens[points].type!=J_ARRAY||j->tokens[points].count<2||j->tokens[points].count>129)return pathReject(c,"Path points required");
    memset(&s->pathActors[slot],0,sizeof(s->pathActors[slot]));s->pathActors[slot].used=1;s->pathActors[slot].id=id;s->pathActors[slot].family=family;s->pathActors[slot].targetId=targetId;s->pathActors[slot].count=j->tokens[points].count;s->pathActors[slot].startUs=s->timeUs;
    int closed=nrField(j,0,"closed");if(closed>=0&&!nrBoolean(j,closed,&s->pathActors[slot].closed))return pathReject(c,"Closed must be boolean");
    int mode=nrField(j,0,"mode");if(mode>=0){const char*modes[]={"clamp","loop","reverse"};int found=0;for(int k=0;k<3;k++)if(nrEqual(j,mode,modes[k])){s->pathActors[slot].mode=k;found=1;}if(!found)return pathReject(c,"Invalid travel mode");}
    if(!pathNumber(j,0,"speed",&s->pathActors[slot].speed,-10000,10000)||!pathNumber(j,0,"distance",&s->pathActors[slot].distance,-1e12,1e12))return pathReject(c,"Travel rate bounds");
    int t=points+1;for(int i=0;i<s->pathActors[slot].count;i++){if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=3)return pathReject(c,"XYZ path point required");int v=t+1;for(int k=0;k<3;k++){double d;if(!nrNumber(j,v,&d)||!(d>=-16000&&d<=16000))return pathReject(c,"Path coordinate bounds");s->pathActors[slot].points[i][k]=d;v=j->tokens[v].next;}t=j->tokens[t].next;}
    if(family==1)for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(s->emitters[i].used&&s->emitters[i].id==targetId)s->pathActors[slot].generation=s->emitters[i].generation;
    if(!pathTarget(s,slot)||!nrValidPathActors(s))return pathReject(c,"Invalid path or missing target");
    if(!family){s->flight.count=0;nrOriginalCameraStop(s);}
    return nrPathActorsTick(s)?0:pathReject(c,"Path target range exceeded");
}

int nrPathTargetPosition(const State*s,int actor,Vec3*out){State*view=(State*)s;Vec3*p=pathTarget(view,actor);if(!p)return 0;*out=*p;return 1;}
