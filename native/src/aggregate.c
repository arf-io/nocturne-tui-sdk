#include "internal.h"
/* Aggregation intentionally discards individual identities. Re-emission creates
 * new particles from captured representative provenance, never current templates. */
static int reject(NrContext*c,const char*why){size_t n=strlen(why);if(n>255)n=255;memcpy(c->error,why,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double low,double high){return nrNumber(j,nrField(j,0,key),out)&&*out>=low&&*out<=high;}
static int vector(const Json*j,int at,Vec3*out){
    if(at<0||j->tokens[at].type!=J_ARRAY||j->tokens[at].count!=3)return 0;
    double x[3];int t=at+1;for(int i=0;i<3;i++){if(!nrNumber(j,t,&x[i])||!(x[i]>=-2000&&x[i]<=2000))return 0;t=j->tokens[t].next;}
    *out=nrV(x[0],x[1],x[2]);return 1;
}
void nrAggregateCapture(State*s,int tile,int slot){
    const Particle*p=&s->particles[slot];const HeatReservoir*h=&s->particleHeat[slot];AggregateProvenance*r=&s->aggregateProvenance[tile];
    memset(r,0,sizeof(*r));r->used=1;r->generation=s->emitters[p->emitterSlot].generation;r->seed=p->seed;r->lifeSteps=p->lifeSteps;
    r->effect=p->effect;r->material=p->material;r->leafShape=p->leafShape;r->size=p->size;r->angle=p->angle;
    r->heatCapacity=h->capacity;r->heatFraction=h->contactFraction;r->heatConductance=h->conductance;
    r->motionAuthored=s->particleMotions[slot].authored;r->orientation=s->particleMotions[slot].orientation;r->angularVelocity=s->particleMotions[slot].angularVelocity;
}
int nrAggregateCompatible(const State*s,int tile,int slot){
    const AggregateProvenance*r=&s->aggregateProvenance[tile];const Particle*p=&s->particles[slot];const HeatReservoir*h=&s->particleHeat[slot];
    /* Keep old snapshot aggregation behavior. Missing provenance stays missing:
     * a later deposit cannot authenticate material already in a legacy tile. */
    if(!r->used)return 1;
    return r->used&&r->generation==s->emitters[p->emitterSlot].generation&&r->effect==p->effect&&r->material==p->material&&r->leafShape==p->leafShape&&r->heatCapacity==h->capacity&&r->heatFraction==h->contactFraction&&r->heatConductance==h->conductance;
}
static Vec3 releasePosition(const State*s,int tile,uint32_t seed){
    const SurfaceTile*g=&s->geometry.tileSurfaces[tile];Vec3 point,normal;
    if(g->surfaceId){double u=nrSqrt(nrRandom(seed,0,201)),v=nrRandom(seed,0,202);point=nrAdd(nrScale(g->a,1-u),nrAdd(nrScale(g->b,u*(1-v)),nrScale(g->c,u*v)));normal=g->normal;}
    else{const DepositTile*t=&s->tiles[tile];point=nrV((t->x+nrRandom(seed,0,201))*s->floor.cellSize,s->floor.height,(t->z+nrRandom(seed,0,202))*s->floor.cellSize);normal=nrV(0,1,0);}
    return nrAdd(point,nrScale(normal,.15));
}
int nrAggregateReemitCommand(NrContext*c,State*s,const Json*j){
    double tileValue=0,countValue=0;Vec3 velocity;int v=nrField(j,0,"velocity");
    if(s->schema<NR_STATE_SCHEMA_AGGREGATE_REEMIT||!nrAllowed(j,0,"op tileIndex count velocity")||!number(j,"tileIndex",&tileValue,0,NR_TILES-1)||tileValue!=(int)tileValue||!number(j,"count",&countValue,1,NR_MAX_PARTICLES)||countValue!=(int)countValue||!vector(j,v,&velocity))return reject(c,"Invalid aggregate re-emission");
    int tile=(int)tileValue,count=(int)countValue;DepositTile*t=&s->tiles[tile];AggregateProvenance*r=&s->aggregateProvenance[tile];SurfaceTile*g=&s->geometry.tileSurfaces[tile];
    int ei=nrFindEmitter(s,(int)t->emitterId);
    if(!t->used||!r->used||countValue>t->count||ei<0||s->emitters[ei].generation!=r->generation)return reject(c,"Aggregate provenance or count unavailable");
    if(g->surfaceId&&(g->meshGeneration!=s->geometry.meshGeneration||g->triangleIndex>=(uint32_t)s->meshCount))return reject(c,"Aggregate contact geometry retired");
    if((uint64_t)s->nextParticle+count>0xffffffffull||(uint64_t)r->emitted+count>0xffffffffull||s->aggregateReemittedCount>0xffffffffffffffffull-(uint64_t)count)return reject(c,"Aggregate identity capacity exhausted");
    int slots[NR_MAX_PARTICLES],available=0;
    for(int i=0;i<(int)NR_MAX_PARTICLES&&available<count;i++)if(!s->particles[i].state)slots[available++]=i;
    if(available<count)return reject(c,"Aggregate particle capacity exhausted");
    HeatReservoir*heat=&s->aggregateHeat[tile];double capacity=heat->capacity/t->count,conductance=heat->conductance/t->count;
    for(int i=0;i<count;i++){
        int slot=slots[i];Particle*p=&s->particles[slot];memset(&s->novaOptics[slot],0,sizeof(NovaOptics));memset(p,0,sizeof(*p));memset(&s->particleMotions[slot],0,sizeof(s->particleMotions[slot]));memset(&s->geometry.particleContacts[slot],0,sizeof(SurfaceContact));memset(&s->sprayParticles[slot],0,sizeof(s->sprayParticles[slot]));memset(&s->particleHeat[slot],0,sizeof(HeatReservoir));
        p->id=s->nextParticle++;p->emitterId=t->emitterId;p->emitterSlot=ei;p->seed=nrHash(r->seed^r->emitted++);p->bornStep=s->step;p->lifeSteps=r->lifeSteps;p->state=1;p->effect=r->effect;p->material=r->material;p->size=r->size;p->angle=r->angle;p->leafShape=r->leafShape;p->heat=1;
        p->position=nrQuantize(releasePosition(s,tile,p->seed));p->previous=p->position;p->velocity=nrQuantize(velocity);
        s->particleMotions[slot].authored=r->motionAuthored;s->particleMotions[slot].orientation=r->orientation;s->particleMotions[slot].angularVelocity=r->angularVelocity;
        if(heat->id)s->particleHeat[slot]=(HeatReservoir){.id=p->id,.capacity=capacity,.temperature=heat->temperature,.contactFraction=r->heatFraction,.conductance=conductance};
    }
    uint32_t remaining=t->count-(uint32_t)count;s->aggregateReemittedCount+=(uint64_t)count;
    if(remaining){heat->capacity=capacity*remaining;heat->conductance=conductance*remaining;t->count=remaining;}
    else{memset(t,0,sizeof(*t));memset(r,0,sizeof(*r));memset(g,0,sizeof(*g));memset(heat,0,sizeof(*heat));}
    return 0;
}
static int boundedVector(Vec3 v,double bound){return v.x>=-bound&&v.x<=bound&&v.y>=-bound&&v.y<=bound&&v.z>=-bound&&v.z<=bound;}
int nrValidAggregateProvenance(const State*s){
    for(int i=0;i<NR_TILES;i++){
        const AggregateProvenance*r=&s->aggregateProvenance[i];
        if(!r->used){AggregateProvenance zero={0};if(memcmp(r,&zero,sizeof(zero)))return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_AGGREGATE_REEMIT||r->used!=1||r->padding||!s->tiles[i].used||!r->generation||r->generation>s->nextEmitterGeneration||!r->lifeSteps||r->lifeSteps>432000||nrEffectFamily(r->effect)!=0||r->material<0||r->material>=NR_MATERIALS||r->leafShape<0||r->leafShape>2||(r->motionAuthored!=0&&r->motionAuthored!=1)||!(r->size>=.005&&r->size<=64)||!(r->angle>=0&&r->angle<=360)||!boundedVector(r->orientation,3600)||!boundedVector(r->angularVelocity,720)||!(r->heatFraction>=0&&r->heatFraction<=1)||!(r->heatConductance>=0&&r->heatConductance<=1000000)||!(r->heatCapacity>=0&&r->heatCapacity<=1000000)||(r->heatCapacity&&r->heatCapacity<.000001))return 0;
        if((r->heatCapacity>0)!=(s->aggregateHeat[i].id!=0))return 0;
    }return 1;
}
