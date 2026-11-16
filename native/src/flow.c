#include "internal.h"
/* Exact linear reservoir response via a scaled matrix exponential. Repeated
 * residence times use the same solver, avoiding singular divided differences. */
static void multiply(double a[12][12],double b[12][12],double out[12][12],int n){
    double r[12][12]={{0}};for(int i=0;i<n;i++)for(int j=0;j<n;j++)for(int k=0;k<n;k++)r[i][j]+=a[i][k]*b[k][j];memcpy(out,r,sizeof(r));
}
static double response(const double*tau,int count,double time,double*flux){
    *flux=0;if(time<0)return 0;if(!count){*flux=1;return time;}if(time==0)return 0;
    int n=count+2;double a[12][12]={{0}},e[12][12]={{0}},term[12][12]={{0}};
    double norm=time;for(int i=0;i<count;i++){a[i][i]=-time/tau[i];if(i)a[i][i-1]=time/tau[i-1];else a[0][n-1]=time;if(time/tau[i]>norm)norm=time/tau[i];}
    a[count][count-1]=time/tau[count-1];int squares=0;while(norm>.25){norm*=.5;squares++;}
    double scale=1;for(int k=0;k<squares;k++)scale*=.5;
    for(int i=0;i<n;i++){e[i][i]=term[i][i]=1;for(int j=0;j<n;j++)a[i][j]*=scale;}
    for(int k=1;k<=24;k++){multiply(term,a,term,n);for(int i=0;i<n;i++)for(int j=0;j<n;j++){term[i][j]/=k;e[i][j]+=term[i][j];}}
    for(int k=0;k<squares;k++)multiply(e,e,e,n);
    *flux=nrClamp(e[count-1][n-1]/tau[count-1],0,1);
    return nrClamp(e[count][n-1],0,time);
}
/* Shared per-stage response kernel. Geometry needs only one stage's flux;
 * conservation queries also accumulate stage volumes without changing math. */
static double stageResponse(const Flow*f,const double*tau,int reservoirs,uint64_t delay,uint64_t timeUs,double*rate){
    double total=0;*rate=0;
    for(int k=0;k<f->epochs;k++){
        uint64_t begin=f->changes[k].atUs,end=k+1<f->epochs?f->changes[k+1].atUs:timeUs;
        double elapsed=timeUs>=begin+delay?(timeUs-begin-delay)/1000000.0:-1;
        double after=k+1<f->epochs&&timeUs>=end+delay?(timeUs-end-delay)/1000000.0:-1;
        double firstRate,lastRate;
        total+=f->changes[k].rate*(response(tau,reservoirs,elapsed,&firstRate)-response(tau,reservoirs,after,&lastRate));
        *rate+=f->changes[k].rate*(firstRate-lastRate);
    }
    *rate=nrClamp(*rate,0,1000000);return total;
}
double nrFlowStageFluxAt(const State*s,int slot,int stage,uint64_t timeUs){
    if(slot<0||slot>=8||!s->flows[slot].used||stage<0||stage>=s->flows[slot].count)return 0;
    const Flow*f=&s->flows[slot];double tau[8],rate;int reservoirs=0;uint64_t delay=0;
    for(int k=0;k<=stage;k++){delay+=f->stages[k].delayUs;if(f->stages[k].tailUs)tau[reservoirs++]=f->stages[k].tailUs/1000000.0;}
    stageResponse(f,tau,reservoirs,delay,timeUs,&rate);return rate;
}
int nrFlowVolumesAt(const State*s,int slot,uint64_t timeUs,double*out){
    const Flow*f=&s->flows[slot];double tau[8];int reservoirs=0;uint64_t delay=0;
    for(int stage=0;stage<=f->count;stage++){
        if(stage){delay+=f->stages[stage-1].delayUs;if(f->stages[stage-1].tailUs)tau[reservoirs++]=f->stages[stage-1].tailUs/1000000.0;}
        double rate,total=stageResponse(f,tau,reservoirs,delay,timeUs,&rate);
        out[9+stage]=rate;out[stage]=stage?nrClamp(total,0,out[stage-1]):total;
    }return 1;
}
int nrFlowVolumes(const State*s,int slot,double*out){return nrFlowVolumesAt(s,slot,s->timeUs,out);}
int nrValidFlows(const State*s){
    for(int i=0;i<8;i++){const Flow*f=&s->flows[i];if(!f->used)continue;
        if(f->used!=1||!f->id||f->id>65535||f->count<1||f->count>8||f->epochs<1||f->epochs>128)return 0;
        for(int j=0;j<i;j++)if(s->flows[j].used&&s->flows[j].id==f->id)return 0;
        for(int k=0;k<f->count;k++){if(!f->stages[k].name[0]||f->stages[k].name[31]||f->stages[k].delayUs>86400000000ull||f->stages[k].tailUs>86400000000ull||(f->stages[k].tailUs&&f->stages[k].tailUs<1000))return 0;for(int j=0;j<k;j++)if(!strcmp(f->stages[j].name,f->stages[k].name))return 0;}
        for(int k=0;k<f->epochs;k++)if(f->changes[k].atUs>s->timeUs||(k&&f->changes[k].atUs<=f->changes[k-1].atUs)||!(f->changes[k].rate>=0&&f->changes[k].rate<=1000000))return 0;
    }
    for(int i=0;i<NR_SURFACES;i++)if(s->flowSurfaces[i].flowId){
        int slot=-1;for(int k=0;k<8;k++)if(s->flows[k].used&&s->flows[k].id==s->flowSurfaces[i].flowId)slot=k;
        if(slot<0||s->flowSurfaces[i].stage<0||s->flowSurfaces[i].stage>=s->flows[slot].count||!(s->flowSurfaces[i].referenceFlux>0&&s->flowSurfaces[i].referenceFlux<=1000000))return 0;
    }return 1;
}
static int reject(NrContext*c,const char*why){size_t n=strlen(why);if(n>255)n=255;memcpy(c->error,why,n);c->error[n]=0;return -1;}
static int integerField(const Json*j,int object,const char*key,uint64_t*out){int token=nrField(j,object,key);double v;if(token<0){*out=0;return 1;}if(!nrNumber(j,token,&v)||!(v>=0&&v<=86400000000.0)||v!=(uint64_t)v)return 0;*out=(uint64_t)v;return 1;}
int nrFlowSetRate(State*s,uint32_t id,double rate){
    if(!(rate>=0&&rate<=1000000))return 0;
    for(int i=0;i<8;i++)if(s->flows[i].used&&s->flows[i].id==id){
        Flow*f=&s->flows[i];int k=f->epochs-1;
        if(f->changes[k].rate==rate)return 1;
        if(f->changes[k].atUs!=s->timeUs){if(f->epochs==128)return 0;k=f->epochs++;}
        f->changes[k].atUs=s->timeUs;f->changes[k].rate=rate;return 1;
    }return 0;
}
int nrFlowCommand(NrContext*c,State*s,const Json*j){
    int change=nrEqual(j,nrField(j,0,"op"),"flow-rate");
    if(!nrAllowed(j,0,change?"op id flux":"op id flux stages"))return reject(c,"Unknown flow field");
    double id,rate;if(!nrNumber(j,nrField(j,0,"id"),&id)||!(id>=1&&id<=65535)||id!=(uint32_t)id||!nrNumber(j,nrField(j,0,"flux"),&rate)||!(rate>=0&&rate<=1000000))return reject(c,"Invalid flow id or flux");
    int slot=-1,freeSlot=-1;for(int i=0;i<8;i++){if(s->flows[i].used&&s->flows[i].id==(uint32_t)id)slot=i;if(!s->flows[i].used&&freeSlot<0)freeSlot=i;}
    if(change)return nrFlowSetRate(s,(uint32_t)id,rate)?0:reject(c,"Unknown flow or rate history capacity");
    if(slot>=0)return reject(c,"Flow already exists; change its rate instead");if(freeSlot<0)return reject(c,"Flow capacity");
    int stages=nrField(j,0,"stages");if(stages<0||j->tokens[stages].type!=J_ARRAY||j->tokens[stages].count<1||j->tokens[stages].count>8)return reject(c,"Flow stages required");
    Flow*f=&s->flows[freeSlot];memset(f,0,sizeof(*f));f->used=1;f->id=(uint32_t)id;f->count=j->tokens[stages].count;f->epochs=1;f->changes[0].atUs=s->timeUs;f->changes[0].rate=rate;
    int t=stages+1;for(int k=0;k<f->count;k++){
        int name=nrField(j,t,"name");if(j->tokens[t].type!=J_OBJECT||!nrAllowed(j,t,"name delayUs tailUs")||name<0||!nrString(j,name,f->stages[k].name,32)||!integerField(j,t,"delayUs",&f->stages[k].delayUs)||!integerField(j,t,"tailUs",&f->stages[k].tailUs))return reject(c,"Invalid flow stage");t=j->tokens[t].next;
    }
    return nrValidFlows(s)?0:reject(c,"Invalid flow stage name or timing");
}

void nrFlowSurfaceAlpha(const State*s,double*out){
    double volumes[8][18];int sampled[8]={0};
    for(int i=0;i<NR_SURFACES;i++){out[i]=1;if(!s->flowSurfaces[i].flowId)continue;
        for(int k=0;k<8;k++)if(s->flows[k].used&&s->flows[k].id==s->flowSurfaces[i].flowId){
            if(!sampled[k]){nrFlowVolumes(s,k,volumes[k]);sampled[k]=1;}
            out[i]=nrClamp(volumes[k][10+s->flowSurfaces[i].stage]/s->flowSurfaces[i].referenceFlux,0,1);break;
        }
    }
}
int nrFlowSurfaceCommand(NrContext*c,State*s,const Json*j){
    int remove=nrEqual(j,nrField(j,0,"op"),"remove-flow-surface");
    if(!nrAllowed(j,0,remove?"op surfaceId":"op surfaceId flowId stage referenceFlux"))return reject(c,"Unknown flow surface field");
    double id;if(!nrNumber(j,nrField(j,0,"surfaceId"),&id)||!(id>=1&&id<=NR_SURFACES)||id!=(int)id)return reject(c,"Invalid flow surface id");int target=(int)id-1;
    if(remove&&s->flowThickness[target].used)return reject(c,"Remove flow thickness before its surface binding");
    if(remove){memset(&s->flowSurfaces[target],0,sizeof(s->flowSurfaces[target]));return 0;}
    double flowId,reference;char stage[32];
    if(!s->geometry.surfaces[target].used||!nrNumber(j,nrField(j,0,"flowId"),&flowId)||!(flowId>=1&&flowId<=65535)||flowId!=(uint32_t)flowId||!nrNumber(j,nrField(j,0,"referenceFlux"),&reference)||!(reference>0&&reference<=1000000)||!nrString(j,nrField(j,0,"stage"),stage,32))return reject(c,"Invalid flow surface binding");
    int index=-1;for(int k=0;k<8;k++)if(s->flows[k].used&&s->flows[k].id==(uint32_t)flowId)for(int n=0;n<s->flows[k].count;n++)if(!strcmp(stage,s->flows[k].stages[n].name))index=n;
    if(index<0)return reject(c,"Unknown flow or stage");
    s->flowSurfaces[target].flowId=(uint32_t)flowId;s->flowSurfaces[target].stage=index;s->flowSurfaces[target].referenceFlux=reference;return 0;
}

static int sinkFlow(const State*s,int sink){for(int i=0;i<8;i++)if(s->flows[i].used&&s->flows[i].id==s->flowSinks[sink].flowId)return i;return -1;}
static double sinkRawStored(const State*s,int flow,uint64_t evaporationUs){
    double tau[9],volume[18],sum=0;int n=0;uint64_t delay=0;const Flow*f=&s->flows[flow];
    for(int i=0;i<f->count;i++){delay+=f->stages[i].delayUs;if(f->stages[i].tailUs)tau[n++]=f->stages[i].tailUs/1000000.0;}
    tau[n++]=evaporationUs/1000000.0;
    for(int k=0;k<f->epochs;k++){uint64_t begin=f->changes[k].atUs,end=k+1<f->epochs?f->changes[k+1].atUs:s->timeUs;double a=s->timeUs>=begin+delay?(s->timeUs-begin-delay)/1000000.0:-1,b=k+1<f->epochs&&s->timeUs>=end+delay?(s->timeUs-end-delay)/1000000.0:-1,rate;sum+=f->changes[k].rate*(response(tau,n,a,&rate)-response(tau,n,b,&rate));}
    nrFlowVolumes(s,flow,volume);return nrClamp(volume[f->count]-sum,0,volume[f->count]);
}
void nrFlowSinkVolumes(const State*s,int sink,double*out){
    int flow=sinkFlow(s,sink);double volume[18];nrFlowVolumes(s,flow,volume);
    double received=nrClamp(volume[s->flows[flow].count]-s->flowSinks[sink].initialReceived,0,1e12),stored=received;
    if(s->flowSinks[sink].evaporationUs){double tau=s->flowSinks[sink].evaporationUs/1000000.0,rate;response(&tau,1,(s->timeUs-s->flowSinks[sink].startUs)/1000000.0,&rate);stored=nrClamp(sinkRawStored(s,flow,s->flowSinks[sink].evaporationUs)-s->flowSinks[sink].initialStored*(1-rate),0,received);}
    out[0]=received*s->flowSinks[sink].fraction;out[1]=stored*s->flowSinks[sink].fraction;out[2]=out[0]-out[1];out[3]=nrClamp(out[1]/s->flowSinks[sink].capacity,0,1);
}
int nrValidFlowSinks(const State*s){
    for(int i=0;i<NR_SURFACES;i++)if(s->flowSinks[i].flowId){
        if(sinkFlow(s,i)<0||s->flowSinks[i].padding||!(s->flowSinks[i].fraction>0&&s->flowSinks[i].fraction<=1)||!(s->flowSinks[i].capacity>0&&s->flowSinks[i].capacity<=1000000)||s->flowSinks[i].startUs>s->timeUs||s->flowSinks[i].evaporationUs>86400000000ull||(s->flowSinks[i].evaporationUs&&s->flowSinks[i].evaporationUs<1000)||!(s->flowSinks[i].initialReceived>=0&&s->flowSinks[i].initialReceived<=86400000000.0)||!(s->flowSinks[i].initialStored>=0&&s->flowSinks[i].initialStored<=s->flowSinks[i].initialReceived))return 0;
        double sum=0;for(int j=0;j<NR_SURFACES;j++)if(s->flowSinks[j].flowId==s->flowSinks[i].flowId)sum+=s->flowSinks[j].fraction;for(int j=0;j<(int)NR_MAX_EMITTERS;j++)if(s->flowSprays[j].flowId==s->flowSinks[i].flowId)sum+=s->flowSprays[j].fraction;if(sum>1)return 0;
    }return 1;
}
int nrFlowSinkCommand(NrContext*c,State*s,const Json*j){
    double id,flowId,fraction,capacity;uint64_t evaporationUs;
    if(!nrAllowed(j,0,"op surfaceId flowId fraction evaporationUs capacity")||!nrNumber(j,nrField(j,0,"surfaceId"),&id)||!(id>=1&&id<=NR_SURFACES)||id!=(int)id||!nrNumber(j,nrField(j,0,"flowId"),&flowId)||!(flowId>=1&&flowId<=65535)||flowId!=(uint32_t)flowId||!nrNumber(j,nrField(j,0,"fraction"),&fraction)||!(fraction>0&&fraction<=1)||!nrNumber(j,nrField(j,0,"capacity"),&capacity)||!(capacity>0&&capacity<=1000000)||!integerField(j,0,"evaporationUs",&evaporationUs))return reject(c,"Invalid flow sink");
    int target=(int)id-1;if(!s->geometry.surfaces[target].used||s->flowSinks[target].flowId)return reject(c,"Flow sink target unavailable");
    s->flowSinks[target].flowId=(uint32_t)flowId;s->flowSinks[target].fraction=fraction;s->flowSinks[target].capacity=capacity;s->flowSinks[target].evaporationUs=evaporationUs;s->flowSinks[target].startUs=s->timeUs;
    if(!nrValidFlowSinks(s))return reject(c,"Invalid sink allocation or evaporation");
    int flow=sinkFlow(s,target);double volume[18];nrFlowVolumes(s,flow,volume);s->flowSinks[target].initialReceived=volume[s->flows[flow].count];s->flowSinks[target].initialStored=evaporationUs?sinkRawStored(s,flow,evaporationUs):0;return 0;
}
static int sprayFlow(const State*s,int emitter){for(int i=0;i<8;i++)if(s->flows[i].used&&s->flows[i].id==s->flowSprays[emitter].flowId)return i;return -1;}
void nrFlowSprayVolumes(const State*s,int emitter,double*out){
    int flow=sprayFlow(s,emitter);double volume[18];nrFlowVolumes(s,flow,volume);
    out[0]=nrClamp(volume[s->flows[flow].count]-s->flowSprays[emitter].initialDelivered,0,86400000000.0)*s->flowSprays[emitter].fraction+s->sprayReentrained[emitter];
    out[1]=s->flowSprays[emitter].emittedVolume;out[2]=nrClamp(out[0]-out[1],0,1e15);
}
int nrFlowSprayDue(const State*s,int emitter){double out[3];nrFlowSprayVolumes(s,emitter,out);double count=out[0]/s->flowSprays[emitter].particleVolume;return count>=1000000000?1000000000:(int)(count+1e-9);}
int nrValidFlowSprays(const State*s){
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(!(s->sprayReentrained[i]>=0&&s->sprayReentrained[i]<=86400000000.0)||(s->sprayReentrained[i]&&!s->flowSprays[i].flowId))return 0;
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(s->flowSprays[i].flowId){
        const Emitter*e=&s->emitters[i];
        if(sprayFlow(s,i)<0||!e->used||e->generation!=s->flowSprays[i].generation||e->count||e->rate||s->flowSprays[i].padding||s->flowSprays[i].ordinal<0||s->flowSprays[i].ordinal>1000000000||e->born!=s->flowSprays[i].ordinal||s->flowSprays[i].startUs>s->timeUs||!(s->flowSprays[i].fraction>0&&s->flowSprays[i].fraction<=1)||!(s->flowSprays[i].particleVolume>=.000000001&&s->flowSprays[i].particleVolume<=1000000)||!(s->flowSprays[i].initialDelivered>=0&&s->flowSprays[i].initialDelivered<=86400000000.0)||s->flowSprays[i].emittedVolume!=s->flowSprays[i].ordinal*s->flowSprays[i].particleVolume)return 0;
        double sum=0;for(int j=0;j<(int)NR_MAX_EMITTERS;j++)if(s->flowSprays[j].flowId==s->flowSprays[i].flowId)sum+=s->flowSprays[j].fraction;
        for(int j=0;j<NR_SURFACES;j++)if(s->flowSinks[j].flowId==s->flowSprays[i].flowId)sum+=s->flowSinks[j].fraction;if(sum>1)return 0;
        double out[3];nrFlowSprayVolumes(s,i,out);if(out[1]>out[0]+1e-8)return 0;
    }return 1;
}
int nrFlowSprayCommand(NrContext*c,State*s,const Json*j){
    double emitterId,flowId,fraction,particleVolume;
    if(!nrAllowed(j,0,"op flowId emitterId fraction particleVolume")||!nrNumber(j,nrField(j,0,"emitterId"),&emitterId)||!(emitterId>=1&&emitterId<=65535)||emitterId!=(uint32_t)emitterId||!nrNumber(j,nrField(j,0,"flowId"),&flowId)||!(flowId>=1&&flowId<=65535)||flowId!=(uint32_t)flowId||!nrNumber(j,nrField(j,0,"fraction"),&fraction)||!(fraction>0&&fraction<=1)||!nrNumber(j,nrField(j,0,"particleVolume"),&particleVolume)||!(particleVolume>=.000000001&&particleVolume<=1000000))return reject(c,"Invalid flow spray");
    int emitter=nrFindEmitter(s,(int)emitterId);if(emitter<0||s->flowSprays[emitter].flowId||s->emitters[emitter].count||s->emitters[emitter].rate||s->emitters[emitter].born)return reject(c,"Spray requires an unused zero-count emitter");
    s->flowSprays[emitter].flowId=(uint32_t)flowId;s->flowSprays[emitter].generation=s->emitters[emitter].generation;s->flowSprays[emitter].fraction=fraction;s->flowSprays[emitter].particleVolume=particleVolume;s->flowSprays[emitter].startUs=s->timeUs;
    int flow=sprayFlow(s,emitter);if(flow<0)return reject(c,"Unknown spray flow");double volume[18];nrFlowVolumes(s,flow,volume);s->flowSprays[emitter].initialDelivered=volume[s->flows[flow].count];
    return nrValidFlowSprays(s)&&nrValidFlowSinks(s)?0:reject(c,"Flow spray allocation rejected");
}
void nrFlowSpraySpawn(State*s,int slot,int emitter){
    memset(&s->sprayParticles[slot],0,sizeof(s->sprayParticles[slot]));
    if(s->flowSprays[emitter].flowId){s->sprayParticles[slot].particleId=s->particles[slot].id;s->sprayParticles[slot].emitterSlot=(uint32_t)emitter;s->sprayParticles[slot].volume=s->flowSprays[emitter].particleVolume;}
}
void nrFlowSprayRelease(State*s,int slot,int kind){
    memset(&s->novaOptics[slot],0,sizeof(NovaOptics));
    if(kind!=1)nrHeatRelease(s,0,slot);
    if(!s->sprayParticles[slot].particleId)return;
    int emitter=(int)s->sprayParticles[slot].emitterSlot;double volume=s->sprayParticles[slot].volume;
    if(kind==1)s->sprayTerminals[emitter].impacted+=volume;else if(kind==2)s->sprayTerminals[emitter].exported+=volume;else s->sprayTerminals[emitter].expired+=volume;
    memset(&s->sprayParticles[slot],0,sizeof(s->sprayParticles[slot]));
}
void nrFlowSprayLifecycle(const State*s,int emitter,double*out){
    out[0]=0;for(int i=0;i<(int)NR_MAX_PARTICLES;i++)if(s->sprayParticles[i].particleId&&s->sprayParticles[i].emitterSlot==(uint32_t)emitter)out[0]+=s->sprayParticles[i].volume;
    out[1]=s->sprayTerminals[emitter].expired;out[2]=s->sprayTerminals[emitter].impacted;out[3]=s->sprayTerminals[emitter].exported;out[4]=s->sprayTerminals[emitter].legacyUnresolved;
}
int nrValidSprayParticles(const State*s){
    if(s->schema<NR_STATE_SCHEMA_SPRAY_PARTICLES)return 1;
    for(int i=0;i<(int)NR_MAX_PARTICLES;i++)if(s->sprayParticles[i].particleId){int emitter=(int)s->sprayParticles[i].emitterSlot;
        if(emitter<0||emitter>=(int)NR_MAX_EMITTERS||!s->flowSprays[emitter].flowId||!s->particles[i].state||s->particles[i].id!=s->sprayParticles[i].particleId||s->particles[i].emitterSlot!=emitter||s->sprayParticles[i].volume!=s->flowSprays[emitter].particleVolume)return 0;
    }
    for(int e=0;e<(int)NR_MAX_EMITTERS;e++){
        if(!(s->sprayTerminals[e].expired>=0&&s->sprayTerminals[e].impacted>=0&&s->sprayTerminals[e].exported>=0&&s->sprayTerminals[e].legacyUnresolved>=0))return 0;
        if(s->flowSprays[e].flowId){double out[5];nrFlowSprayLifecycle(s,e,out);double total=out[0]+out[1]+out[2]+out[3]+out[4];if(nrAbs(total-s->flowSprays[e].emittedVolume)>1e-8*(1+s->flowSprays[e].emittedVolume))return 0;}
    }return 1;
}

void nrFlowSprayPromote(State*s){if(s->schema==NR_STATE_SCHEMA_FLOW_SPRAY)for(int i=0;i<(int)NR_MAX_EMITTERS;i++)s->sprayTerminals[i].legacyUnresolved=s->flowSprays[i].emittedVolume;}
void nrSurfaceWaterCell(const State*s,int triangle,double*out){
    out[0]=out[1]=out[2]=0;int id=s->surfaceWater.cells[triangle].surfaceId;if(!id)return;
    double stored=s->surfaceWater.cells[triangle].stored;
    uint64_t evaporation=s->surfaceWater.settings[id-1].evaporationUs;
    if(evaporation){double tau=evaporation/1000000.0,rate;response(&tau,1,(s->timeUs-s->surfaceWater.cells[triangle].atUs)/1000000.0,&rate);stored*=1-rate;}
    out[0]=s->surfaceWater.cells[triangle].received;out[1]=stored;out[2]=nrClamp(stored/s->surfaceWater.settings[id-1].capacity,0,1);
}
int nrWaterSample(const NrContext*c,uint32_t index,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||index>=(uint32_t)c->state.meshCount||!out||capacity<8||((uintptr_t)out%8))return -1;
    const State*s=&c->state;int id=s->geometry.triangleSurfaces[index];
    if(id<1||id>NR_SURFACES||!s->surfaceWater.settings[id-1].used)return 0;
    if(!nrExternalOutput(c,out,8*sizeof(double)))return -1;
    double cell[3];nrSurfaceWaterCell(s,(int)index,cell);
    double incoming=s->waterTransfers[index].incoming,outgoing=s->waterTransfers[index].outgoing;
    double row[8]={id,cell[0]-incoming,cell[1],cell[2],incoming,outgoing,cell[0]-cell[1]-outgoing,s->surfaceWater.settings[id-1].capacity};
    memcpy(out,row,sizeof(row));return 1;
}
void nrSurfaceWaterTotals(const State*s,int surface,double*out){
    out[0]=s->surfaceWater.settings[surface].historicalReceived;out[1]=0;out[2]=s->surfaceWater.settings[surface].historicalEvaporated;out[3]=s->surfaceWater.settings[surface].historicalExported;out[4]=s->waterHistoricalTransfers[surface].incoming;out[5]=s->waterHistoricalTransfers[surface].outgoing;
    for(int i=0;i<NR_MESH;i++)if(s->surfaceWater.cells[i].surfaceId==(uint32_t)(surface+1)){double cell[3];nrSurfaceWaterCell(s,i,cell);out[0]+=cell[0]-s->waterTransfers[i].incoming;out[1]+=cell[1];out[2]+=cell[0]-cell[1]-s->waterTransfers[i].outgoing;out[4]+=s->waterTransfers[i].incoming;out[5]+=s->waterTransfers[i].outgoing;}
}
void nrSurfaceWaterImpact(State*s,int particle,const GeometryHit*hit){
    if(!hit||!hit->surfaceId||hit->triangleIndex>=NR_MESH||!s->surfaceWater.settings[hit->surfaceId-1].used||!s->sprayParticles[particle].particleId)return;
    int index=(int)hit->triangleIndex;nrSettleWaterHeat(s,index);double cell[3];nrSurfaceWaterCell(s,index,cell);double volume=s->sprayParticles[particle].volume;
    s->surfaceWater.cells[index].surfaceId=hit->surfaceId;s->surfaceWater.cells[index].atUs=s->timeUs;s->surfaceWater.cells[index].received=cell[0]+volume;s->surfaceWater.cells[index].stored=cell[1]+volume;
}
void nrSurfaceWaterMeshChanged(State*s,int append,int base){
    if(append){memset(&s->latentHeat[base],0,(size_t)(s->meshCount-base)*sizeof(s->latentHeat[0]));}
    else{for(int i=0;i<NR_MESH;i++){nrSettleWaterHeat(s,i);s->historicalLatentEnergy+=s->latentHeat[i].evaporatedEnergy;}memset(s->latentHeat,0,sizeof(s->latentHeat));}

    if(append){for(int i=0;i<64;i++)if(s->waterLinks[i].used)s->waterLinks[i].generation=s->geometry.meshGeneration+1;}else {memset(s->waterLinks,0,sizeof(s->waterLinks));memset(s->waterLinkHeatCapacity,0,sizeof(s->waterLinkHeatCapacity));}
    if(append){memset(&s->waterTransfers[base],0,(size_t)(s->meshCount-base)*sizeof(s->waterTransfers[0]));memset(&s->surfaceWater.cells[base],0,(size_t)(s->meshCount-base)*sizeof(s->surfaceWater.cells[0]));return;}
    for(int i=0;i<NR_MESH;i++)if(s->surfaceWater.cells[i].surfaceId){int surface=(int)s->surfaceWater.cells[i].surfaceId-1;double cell[3];nrSurfaceWaterCell(s,i,cell);s->surfaceWater.settings[surface].historicalReceived+=cell[0]-s->waterTransfers[i].incoming;s->surfaceWater.settings[surface].historicalEvaporated+=cell[0]-cell[1]-s->waterTransfers[i].outgoing;s->surfaceWater.settings[surface].historicalExported+=cell[1];s->waterHistoricalTransfers[surface].incoming+=s->waterTransfers[i].incoming;s->waterHistoricalTransfers[surface].outgoing+=s->waterTransfers[i].outgoing;}
    memset(s->surfaceWater.cells,0,sizeof(s->surfaceWater.cells));memset(s->waterTransfers,0,sizeof(s->waterTransfers));
}
int nrValidSurfaceWater(const State*s){
    for(int i=0;i<NR_MESH;i++)if(!(s->waterTransfers[i].incoming>=0&&s->waterTransfers[i].incoming<=1e15&&s->waterTransfers[i].outgoing>=0&&s->waterTransfers[i].outgoing<=1e15)||((s->waterTransfers[i].incoming||s->waterTransfers[i].outgoing)&&!s->surfaceWater.cells[i].surfaceId))return 0;
    for(int i=0;i<NR_SURFACES;i++)if(!(s->waterHistoricalTransfers[i].incoming>=0&&s->waterHistoricalTransfers[i].incoming<=1e15&&s->waterHistoricalTransfers[i].outgoing>=0&&s->waterHistoricalTransfers[i].outgoing<=1e15)||((s->waterHistoricalTransfers[i].incoming||s->waterHistoricalTransfers[i].outgoing)&&!s->surfaceWater.settings[i].used))return 0;
    for(int i=0;i<NR_SURFACES;i++)if(s->surfaceWater.settings[i].used){
        if(s->surfaceWater.settings[i].used!=1||s->surfaceWater.settings[i].padding||!(s->surfaceWater.settings[i].capacity>0&&s->surfaceWater.settings[i].capacity<=1000000)||s->surfaceWater.settings[i].evaporationUs>86400000000ull||(s->surfaceWater.settings[i].evaporationUs&&s->surfaceWater.settings[i].evaporationUs<1000)||!(s->surfaceWater.settings[i].historicalReceived>=0&&s->surfaceWater.settings[i].historicalReceived<=86400000000.0)||!(s->surfaceWater.settings[i].historicalEvaporated>=0)||!(s->surfaceWater.settings[i].historicalExported>=0)||nrAbs(s->surfaceWater.settings[i].historicalReceived+s->waterHistoricalTransfers[i].incoming-s->surfaceWater.settings[i].historicalEvaporated-s->surfaceWater.settings[i].historicalExported-s->waterHistoricalTransfers[i].outgoing)>1e-8*(1+s->surfaceWater.settings[i].historicalReceived))return 0;
    }
    for(int i=0;i<NR_MESH;i++)if(s->surfaceWater.cells[i].surfaceId){int id=(int)s->surfaceWater.cells[i].surfaceId;
        if(id<1||id>NR_SURFACES||i>=s->meshCount||!s->surfaceWater.settings[id-1].used||s->geometry.triangleSurfaces[i]!=id||s->surfaceWater.cells[i].padding||s->surfaceWater.cells[i].atUs>s->timeUs||!(s->surfaceWater.cells[i].received>=0&&s->surfaceWater.cells[i].received<=86400000000.0)||!(s->surfaceWater.cells[i].stored>=0&&s->surfaceWater.cells[i].stored<=s->surfaceWater.cells[i].received)||!(s->waterTransfers[i].incoming>=0&&s->waterTransfers[i].incoming<=s->surfaceWater.cells[i].received)||!(s->waterTransfers[i].outgoing>=0&&s->waterTransfers[i].outgoing<=s->surfaceWater.cells[i].received-s->surfaceWater.cells[i].stored+1e-8*(1+s->surfaceWater.cells[i].received)))return 0;
    }return 1;
}
int nrBindWaterValue(State*s,const Value*v,double x){
    int index=v->bindingId-1;
    if(index<0||index>=NR_SURFACES||!s->geometry.surfaces[index].used||!s->surfaceWater.settings[index].used)return 0;
    int capacity=!strcmp(v->field,"water.capacity"),evaporation=!strcmp(v->field,"water.evaporationUs");
    if((!capacity&&!evaporation)||!nrValueNumberValid(v,x))return 0;
    if((capacity&&s->surfaceWater.settings[index].capacity==x)||(evaporation&&s->surfaceWater.settings[index].evaporationUs==(uint64_t)x))return 1;
    for(int i=0;i<s->meshCount;i++)if(s->surfaceWater.cells[i].surfaceId==(uint32_t)v->bindingId){
        nrSettleWaterHeat(s,i);double cell[3];nrSurfaceWaterCell(s,i,cell);s->surfaceWater.cells[i].stored=cell[1];s->surfaceWater.cells[i].atUs=s->timeUs;
    }
    if(capacity)s->surfaceWater.settings[index].capacity=x;else s->surfaceWater.settings[index].evaporationUs=(uint64_t)x;
    return nrValidSurfaceWater(s);
}
int nrSurfaceWaterSettingsShape(const Json*j){
    double id,capacity=1;uint64_t evaporation=0;
    return nrEqual(j,nrField(j,0,"op"),"surface-water-settings")&&nrAllowed(j,0,"op surfaceId capacity evaporationUs")&&
        nrNumber(j,nrField(j,0,"surfaceId"),&id)&&id>=1&&id<=NR_SURFACES&&id==(int)id&&
        (nrField(j,0,"capacity")>=0||nrField(j,0,"evaporationUs")>=0)&&
        (nrField(j,0,"capacity")<0||(nrNumber(j,nrField(j,0,"capacity"),&capacity)&&capacity>0&&capacity<=1000000))&&
        (nrField(j,0,"evaporationUs")<0||(integerField(j,0,"evaporationUs",&evaporation)&&(!evaporation||evaporation>=1000)&&evaporation<=86400000000ull));
}
int nrSurfaceWaterSettingsCommand(NrContext*c,State*s,const Json*j){
    if(!nrSurfaceWaterSettingsShape(j))return reject(c,"Invalid water response settings");
    double id;nrNumber(j,nrField(j,0,"surfaceId"),&id);int index=(int)id-1;
    if(!s->geometry.surfaces[index].used||!s->surfaceWater.settings[index].used)return reject(c,"Water response surface unavailable");
    for(int i=0;i<s->meshCount;i++)if(s->surfaceWater.cells[i].surfaceId==(uint32_t)id){
        nrSettleWaterHeat(s,i);double cell[3];nrSurfaceWaterCell(s,i,cell);s->surfaceWater.cells[i].stored=cell[1];s->surfaceWater.cells[i].atUs=s->timeUs;
    }
    if(nrField(j,0,"capacity")>=0)nrNumber(j,nrField(j,0,"capacity"),&s->surfaceWater.settings[index].capacity);
    if(nrField(j,0,"evaporationUs")>=0)integerField(j,0,"evaporationUs",&s->surfaceWater.settings[index].evaporationUs);
    return nrValidSurfaceWater(s)?0:reject(c,"Water response ledger rejected");
}
int nrSurfaceWaterAddShape(const Json*j){
    double triangle,volume;
    return nrEqual(j,nrField(j,0,"op"),"surface-water-add")&&nrAllowed(j,0,"op triangleIndex volume")&&
        nrNumber(j,nrField(j,0,"triangleIndex"),&triangle)&&triangle>=0&&triangle<NR_MESH&&triangle==(int)triangle&&
        nrNumber(j,nrField(j,0,"volume"),&volume)&&volume>0&&volume<=1000000;
}
int nrSurfaceWaterAddCommand(NrContext*c,State*s,const Json*j){
    if(!nrSurfaceWaterAddShape(j))return reject(c,"Invalid authored water volume or triangle");
    double triangle,volume;nrNumber(j,nrField(j,0,"triangleIndex"),&triangle);nrNumber(j,nrField(j,0,"volume"),&volume);int index=(int)triangle;
    if(index>=s->meshCount)return reject(c,"Authored water triangle unavailable");
    int id=s->geometry.triangleSurfaces[index];
    if(id<1||id>NR_SURFACES||!s->surfaceWater.settings[id-1].used)return reject(c,"Authored water surface not configured");
    nrSettleWaterHeat(s,index);double cell[3];nrSurfaceWaterCell(s,index,cell);
    s->surfaceWater.cells[index].surfaceId=(uint32_t)id;s->surfaceWater.cells[index].atUs=s->timeUs;
    s->surfaceWater.cells[index].received=cell[0]+volume;s->surfaceWater.cells[index].stored=cell[1]+volume;
    return nrValidSurfaceWater(s)?0:reject(c,"Authored water ledger range exceeded");
}
int nrSurfaceWaterCommand(NrContext*c,State*s,const Json*j){
    double id,capacity;uint64_t evaporation;
    if(!nrAllowed(j,0,"op surfaceId capacity evaporationUs")||!nrNumber(j,nrField(j,0,"surfaceId"),&id)||!(id>=1&&id<=NR_SURFACES)||id!=(int)id||!nrNumber(j,nrField(j,0,"capacity"),&capacity)||!(capacity>0&&capacity<=1000000)||!integerField(j,0,"evaporationUs",&evaporation))return reject(c,"Invalid surface water configuration");
    int index=(int)id-1;if(!s->geometry.surfaces[index].used||s->surfaceWater.settings[index].used)return reject(c,"Surface water target unavailable or already configured");
    s->surfaceWater.settings[index].used=1;s->surfaceWater.settings[index].capacity=capacity;s->surfaceWater.settings[index].evaporationUs=evaporation;return nrValidSurfaceWater(s)?0:reject(c,"Invalid water evaporation time");
}
int nrSurfaceWaterTransferCommand(NrContext*c,State*s,const Json*j){
    double from,to,volume;
    if(!nrAllowed(j,0,"op fromTriangle toTriangle volume heatCapacityPerVolume")||!nrNumber(j,nrField(j,0,"fromTriangle"),&from)||!(from>=0&&from<s->meshCount)||from!=(int)from||!nrNumber(j,nrField(j,0,"toTriangle"),&to)||!(to>=0&&to<s->meshCount)||to!=(int)to||from==to||!nrNumber(j,nrField(j,0,"volume"),&volume)||!(volume>0&&volume<=1000000))return reject(c,"Invalid surface water transfer");
    int a=(int)from,b=(int)to,id=s->geometry.triangleSurfaces[b];nrSettleWaterHeat(s,a);nrSettleWaterHeat(s,b);double source[3],target[3];nrSurfaceWaterCell(s,a,source);nrSurfaceWaterCell(s,b,target);
    if(!id||!s->surfaceWater.settings[id-1].used||source[1]<volume)return reject(c,"Water transfer target unavailable or insufficient water");
    int heatField=nrField(j,0,"heatCapacityPerVolume");
    if(heatField>=0){
        double coefficient,thermal[4];
        if(!nrNumber(j,heatField,&coefficient)||!(coefficient>0&&coefficient<=1e9))return reject(c,"Invalid water heat capacity");
        if(!s->thermalCells[a].used||!s->thermalCells[b].used)return reject(c,"Water heat transfer cells unavailable");
        nrThermalCell(s,a,thermal);
        int result=nrTransferThermalEnergy(c,s,a,b,volume*coefficient*thermal[0]);if(result)return result;
    }
    s->surfaceWater.cells[a].stored=source[1]-volume;s->surfaceWater.cells[a].atUs=s->timeUs;s->waterTransfers[a].outgoing+=volume;
    s->surfaceWater.cells[b].surfaceId=(uint32_t)id;s->surfaceWater.cells[b].received=target[0]+volume;s->surfaceWater.cells[b].stored=target[1]+volume;s->surfaceWater.cells[b].atUs=s->timeUs;s->waterTransfers[b].incoming+=volume;
    return nrValidSurfaceWater(s)?0:reject(c,"Water transfer ledger rejected");
}
int nrValidWaterLinks(const State*s){
    for(int i=0;i<64;i++){
        double cp=s->waterLinkHeatCapacity[i];if(!(cp>=0&&cp<=1e9)||(!s->waterLinks[i].used&&cp!=0))return 0;
        if(!s->waterLinks[i].used)continue;
        int a=s->waterLinks[i].from,b=s->waterLinks[i].to;
        if(s->waterLinks[i].used!=1||!s->waterLinks[i].id||s->waterLinks[i].id>65535||s->waterLinks[i].generation!=s->geometry.meshGeneration||s->waterLinks[i].padding||s->waterLinks[i].startUs>s->timeUs||a<0||b<0||a>=s->meshCount||b>=s->meshCount||a==b||!(s->waterLinks[i].rate>0&&s->waterLinks[i].rate<=1000))return 0;
        if(cp>0&&(!s->thermalCells[a].used||!s->thermalCells[b].used))return 0;
        int from=s->geometry.triangleSurfaces[a],to=s->geometry.triangleSurfaces[b];if(!from||!to||!s->surfaceWater.settings[from-1].used||!s->surfaceWater.settings[to-1].used)return 0;
        for(int j=0;j<i;j++)if(s->waterLinks[j].used&&(s->waterLinks[j].id==s->waterLinks[i].id||(s->waterLinks[j].from==a&&s->waterLinks[j].to==b)))return 0;
    }return 1;
}
int nrSurfaceWaterLinkCommand(NrContext*c,State*s,const Json*j){
    int remove=nrEqual(j,nrField(j,0,"op"),"remove-surface-water-link");double id;
    if(!nrAllowed(j,0,remove?"op id":"op id fromTriangle toTriangle rate heatCapacityPerVolume")||!nrNumber(j,nrField(j,0,"id"),&id)||!(id>=1&&id<=65535)||id!=(uint32_t)id)return reject(c,"Invalid water link id");
    int slot=-1,freeSlot=-1;for(int i=0;i<64;i++){if(s->waterLinks[i].used&&s->waterLinks[i].id==(uint32_t)id)slot=i;if(!s->waterLinks[i].used&&freeSlot<0)freeSlot=i;}
    if(remove){if(slot>=0){memset(&s->waterLinks[slot],0,sizeof(s->waterLinks[slot]));s->waterLinkHeatCapacity[slot]=0;}return 0;}
    double a,b,rate;if(!nrNumber(j,nrField(j,0,"fromTriangle"),&a)||!(a>=0&&a<s->meshCount)||a!=(int)a||!nrNumber(j,nrField(j,0,"toTriangle"),&b)||!(b>=0&&b<s->meshCount)||b!=(int)b||a==b||!nrNumber(j,nrField(j,0,"rate"),&rate)||!(rate>0&&rate<=1000))return reject(c,"Invalid water link parameters");
    double cp=0;int field=nrField(j,0,"heatCapacityPerVolume");if(field>=0&&(s->schema<NR_STATE_SCHEMA_HYDRAULIC_HEAT||!nrNumber(j,field,&cp)||!(cp>0&&cp<=1e9)))return reject(c,"Invalid hydraulic heat capacity");
    if(slot<0)slot=freeSlot;if(slot<0)return reject(c,"Water link capacity");memset(&s->waterLinks[slot],0,sizeof(s->waterLinks[slot]));s->waterLinks[slot].used=1;s->waterLinks[slot].id=(uint32_t)id;s->waterLinks[slot].generation=s->geometry.meshGeneration;s->waterLinks[slot].from=(int)a;s->waterLinks[slot].to=(int)b;s->waterLinks[slot].rate=rate;s->waterLinkHeatCapacity[slot]=cp;s->waterLinks[slot].startUs=s->timeUs;return nrValidWaterLinks(s)?0:reject(c,"Water link targets unavailable or duplicate");
}
int nrSurfaceWaterTransport(State*s){
    double rates[NR_MESH]={0},stored[NR_MESH]={0},outgoing[NR_MESH]={0},incoming[NR_MESH]={0},remaining[NR_MESH]={0};int count[NR_MESH]={0},any=0;double hazards[64]={0};
    for(int i=0;i<64;i++)if(s->waterLinks[i].used){int a=s->waterLinks[i].from;double start=(s->step-1)/120.0,epoch=s->waterLinks[i].startUs/1000000.0;if(epoch>start)start=epoch;double elapsed=s->waterLinks[i].startUs>=s->timeUs?0:s->step/120.0-start;hazards[i]=s->waterLinks[i].rate*nrClamp(elapsed,0,1.0/120);if(hazards[i]>0){rates[a]+=hazards[i];count[a]++;any=1;}}
    if(!any)return 1;
    for(int i=0;i<64;i++)if(hazards[i]>0){nrSettleWaterHeat(s,s->waterLinks[i].from);nrSettleWaterHeat(s,s->waterLinks[i].to);}
    double heatIn[NR_MESH]={0},heatOut[NR_MESH]={0},thermal[NR_MESH][4];int thermalTouched[NR_MESH]={0};
    for(int i=0;i<64;i++)if(hazards[i]>0&&s->waterLinkHeatCapacity[i]>0){int a=s->waterLinks[i].from,b=s->waterLinks[i].to;thermalTouched[a]=thermalTouched[b]=1;}
    for(int i=0;i<s->meshCount;i++)if(thermalTouched[i]){if(!s->thermalCells[i].used)return 0;nrThermalCell(s,i,thermal[i]);}
    for(int i=0;i<s->meshCount;i++){double cell[3];nrSurfaceWaterCell(s,i,cell);stored[i]=cell[1];if(rates[i]>0){double tau=1/rates[i],fraction;response(&tau,1,1,&fraction);outgoing[i]=remaining[i]=stored[i]*fraction;}}
    for(int i=0;i<64;i++)if(hazards[i]>0){int a=s->waterLinks[i].from,b=s->waterLinks[i].to;count[a]--;double volume=count[a]?nrClamp(outgoing[a]*hazards[i]/rates[a],0,remaining[a]):remaining[a];remaining[a]-=volume;incoming[b]+=volume;
        if(s->waterLinkHeatCapacity[i]>0){double energy=volume*s->waterLinkHeatCapacity[i]*thermal[a][0];if(!(energy>=0&&energy<=1e10))return 0;heatOut[a]+=energy;heatIn[b]+=energy;}
    }
    for(int i=0;i<s->meshCount;i++)if(thermalTouched[i]){
        double energy=thermal[i][1]-heatOut[i]+heatIn[i],temperature=energy/s->thermalCells[i].capacity;
        if(!(heatOut[i]<=thermal[i][1])||!(temperature>=0&&temperature<=10000))return 0;
    }
    for(int i=0;i<s->meshCount;i++)if(thermalTouched[i]){
        s->thermalCells[i].atUs=s->timeUs;s->thermalCells[i].appliedEnergy=thermal[i][2];s->thermalCells[i].environmentEnergy=thermal[i][3];
        s->thermalCells[i].temperature=(thermal[i][1]-heatOut[i]+heatIn[i])/s->thermalCells[i].capacity;
        s->thermalTransfers[i].incoming+=heatIn[i];s->thermalTransfers[i].outgoing+=heatOut[i];
    }
    for(int i=0;i<s->meshCount;i++)if(outgoing[i]||incoming[i]){
        s->surfaceWater.cells[i].surfaceId=(uint32_t)s->geometry.triangleSurfaces[i];s->surfaceWater.cells[i].atUs=s->timeUs;s->surfaceWater.cells[i].stored=nrClamp(stored[i]-outgoing[i]+incoming[i],0,86400000000.0);s->surfaceWater.cells[i].received+=incoming[i];s->waterTransfers[i].incoming+=incoming[i];s->waterTransfers[i].outgoing+=outgoing[i];
    }return nrValidSurfaceWater(s)&&nrValidThermal(s);
}

int nrSurfaceWaterReemitCommand(NrContext*c,State*s,const Json*j){
    double triangle,emitterId,volume;
    if(!nrAllowed(j,0,"op triangleIndex emitterId volume")||!nrNumber(j,nrField(j,0,"triangleIndex"),&triangle)||!(triangle>=0&&triangle<s->meshCount)||triangle!=(int)triangle||!nrNumber(j,nrField(j,0,"emitterId"),&emitterId)||!(emitterId>=1&&emitterId<=65535)||emitterId!=(int)emitterId||!nrNumber(j,nrField(j,0,"volume"),&volume)||!(volume>0&&volume<=1000000))return reject(c,"Invalid water re-emission");
    int emitter=nrFindEmitter(s,(int)emitterId),index=(int)triangle;nrSettleWaterHeat(s,index);double cell[3];nrSurfaceWaterCell(s,index,cell);
    if(emitter<0||!s->flowSprays[emitter].flowId||s->emitters[emitter].stopping||cell[1]<volume||s->sprayReentrained[emitter]+volume>86400000000.0)return reject(c,"Re-emission target unavailable or insufficient water");
    s->surfaceWater.cells[index].stored=cell[1]-volume;s->surfaceWater.cells[index].atUs=s->timeUs;s->waterTransfers[index].outgoing+=volume;s->sprayReentrained[emitter]+=volume;
    return nrValidSurfaceWater(s)&&nrValidFlowSprays(s)?0:reject(c,"Water re-emission ledger rejected");
}
