#include "internal.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double lo,double hi){int t=nrField(j,0,key);if(t<0)return 1;double v;if(!nrNumber(j,t,&v)||!(v>=lo&&v<=hi))return 0;*out=v;return 1;}
BurstControls nrBurstControls(const State*s,int emitter){
    if(s->burstControls[emitter].used)return s->burstControls[emitter];
    BurstControls result={.used=1,.glitterHz=18,.glitterDepth=.6,.coreAlpha=1,.residualAlpha=1,.residualUs=180000};return result;
}
int nrValidBurstControls(const State*s){
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++){
        const BurstControls*b=&s->burstControls[i];if(!b->used)continue;
        if(b->used!=1||b->reserved||s->schema<NR_STATE_SCHEMA_BURST_CONTROLS||!s->emitters[i].used||nrEffectAlgorithm(s->emitters[i].effect)!=4||
           !(b->glitterHz>=0&&b->glitterHz<=60)||!(b->glitterDepth>=0&&b->glitterDepth<=1)||!(b->coreAlpha>=0&&b->coreAlpha<=1)||!(b->residualAlpha>=0&&b->residualAlpha<=1)||b->residualUs<1000||b->residualUs>10000000)return 0;
    }return 1;
}
int nrBurstStyleCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_BURST_CONTROLS)return reject(c,"Burst style requires schema53");
    if(!nrAllowed(j,0,"op id glitterHz glitterDepth coreAlpha residualMs residualAlpha coreMs"))return reject(c,"Unknown burst style field");
    double id=0;if(nrField(j,0,"id")<0||!number(j,"id",&id,1,65535)||id!=(uint32_t)id)return reject(c,"Burst emitter id required");
    int slot=nrFindEmitter(s,(int)id);if(slot<0||nrEffectAlgorithm(s->emitters[slot].effect)!=4)return reject(c,"Burst style requires a firework emitter");
    BurstControls b=nrBurstControls(s,slot);double residual=b.residualUs/1000.0,core=s->emitters[slot].coreUs/1000.0;
    if(!number(j,"glitterHz",&b.glitterHz,0,60)||!number(j,"glitterDepth",&b.glitterDepth,0,1)||!number(j,"coreAlpha",&b.coreAlpha,0,1)||!number(j,"residualAlpha",&b.residualAlpha,0,1)||
       !number(j,"residualMs",&residual,1,10000)||residual*1000!=(uint64_t)(residual*1000)||!number(j,"coreMs",&core,0,10000)||core*1000!=(uint32_t)(core*1000))return reject(c,"Invalid burst style setting");
    b.residualUs=(uint64_t)(residual*1000);s->burstControls[slot]=b;s->emitters[slot].coreUs=(uint32_t)(core*1000);return 0;
}
/* Staged numeric edits share the public command's domains and never touch
 * living particle records. Registration is wired at the batch boundary. */
int nrBurstBindingField(const char*field){
    return !strcmp(field,"glitterHz")||!strcmp(field,"glitterDepth")||!strcmp(field,"coreAlpha")||!strcmp(field,"residualMs")||!strcmp(field,"residualAlpha");
}
int nrBindBurstValue(State*s,const Value*v,double x){
    int slot=nrFindEmitter(s,v->bindingId);
    if(slot<0||s->schema<NR_STATE_SCHEMA_BURST_CONTROLS||
       nrEffectAlgorithm(s->emitters[slot].effect)!=4)return 0;
    BurstControls b=nrBurstControls(s,slot);int matched=0;
#define SCALAR(name,member,maximum) if(!strcmp(v->field,name)){if(!(x>=0&&x<=maximum))return 0;b.member=x;matched=1;}
    SCALAR("glitterHz",glitterHz,60)
    SCALAR("glitterDepth",glitterDepth,1)
    SCALAR("coreAlpha",coreAlpha,1)
    SCALAR("residualAlpha",residualAlpha,1)
#undef SCALAR
    if(!strcmp(v->field,"residualMs")){
        double us=x*1000;
        if(!(x>=1&&x<=10000)||us!=(uint64_t)us)return 0;
        b.residualUs=(uint64_t)us;matched=1;
    }
    if(!matched)return 0;s->burstControls[slot]=b;return 1;
}
static double decay(double x){
    if(x>745)return 0;int squares=0;while(x>.125){x*=.5;squares++;}
    double result=1,term=1;for(int k=1;k<=20;k++){term*= -x/k;result+=term;}
    for(int k=0;k<squares;k++)result*=result;return result;
}
int nrBurstAppearance(const State*s,int index,double out[4]){
    if(index<0||index>=(int)NR_MAX_PARTICLES)return 0;const Particle*p=&s->particles[index];
    if(p->state!=1||nrEffectAlgorithm(p->effect)!=4)return 0;
    const Emitter*e=&s->emitters[p->emitterSlot];BurstControls b=nrBurstControls(s,p->emitterSlot);
    double age=(s->step-p->bornStep)/120.0,life=p->lifeSteps/120.0,remaining=nrClamp(1-age/life,0,1),fade=remaining*nrSqrt(remaining);
    uint32_t salt=(uint32_t)nrFloor(age*b.glitterHz)+100;
    /* Original Kinetic rand: captured native birth seed, one local sample index.
     * This retains its exact hash32/randomAt salt and full uint32 precision. */
    double random=nrHash(p->seed^(salt*2246822519u)^2654435761u)/4294967296.0;
    out[0]=age*1000000;
    out[1]=e->coreUs?nrSqrt(nrClamp(1-age*1000000/e->coreUs,0,1))*b.coreAlpha:0;
    out[2]=fade*(s->reducedMotion?1:1-b.glitterDepth+b.glitterDepth*random);
    out[3]=e->coreUs&&age*1000000<e->coreUs*2.0?decay(age*1000000/b.residualUs)*b.residualAlpha:0;
    return 1;
}
