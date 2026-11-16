#include "internal.h"
int nrEndStyleSupported(int effect,int style) {
    int algorithm=nrEffectAlgorithm(effect);
    return style!=4||algorithm==3||algorithm==4||algorithm==5;
}
static int allocate(State*s) {
    for(int i=0; i<(int)NR_MAX_PARTICLES; i++)if(!s->particles[i].state)return i;
    return -1;
}
static double depositFade(uint64_t now,uint64_t at,uint64_t retention,uint64_t fade) {
    if(!retention||!fade)return 1;
    uint64_t age=now>=at?now-at:0;
    if(age>=retention)return 0;
    return nrClamp((double)(retention-age)/fade,0,1);
}
static double randomSigned(uint32_t seed,uint32_t id,uint32_t k) {
    return nrRandom(seed,id,k)*2-1;
}
static Vec3 randomUnit(uint32_t seed,uint32_t id) {
    Vec3 r=nrV(randomSigned(seed,id,100),randomSigned(seed,id,101),randomSigned(seed,id,102));
    return nrNormal(r);
}
static Vec3 birthTransform(Vec3 v,Vec3 angles) {
    /* Right-handed active rotations, Rx then Ry then Rz. Zero is exact identity. */
    if(!angles.x&&!angles.y&&!angles.z)return v;
    double c=nrCos(angles.x),s=nrSin(angles.x);
    v=nrV(v.x,c*v.y-s*v.z,s*v.y+c*v.z);
    c=nrCos(angles.y);s=nrSin(angles.y);
    v=nrV(c*v.x+s*v.z,v.y,-s*v.x+c*v.z);
    c=nrCos(angles.z);s=nrSin(angles.z);
    return nrV(c*v.x-s*v.y,s*v.x+c*v.y,v.z);
}
static void spawn(State*s,int ei,int ordinal,int slot) {
    Emitter*e=&s->emitters[ei];
    Particle*p=&s->particles[slot];
    memset(p,0,sizeof(*p));
    memset(&s->novaOptics[slot],0,sizeof(NovaOptics));
    memcpy(&s->particleMotions[slot],&s->emitterMotions[ei],sizeof(s->particleMotions[slot]));
    memset(&s->geometry.particleContacts[slot],0,sizeof(SurfaceContact));
    p->id=s->nextParticle++;
    nrFlowSpraySpawn(s,slot,ei);
    p->emitterId=e->id;
    p->emitterSlot=ei;
    p->seed=nrHash(e->seed^(uint32_t)ordinal);
    p->bornStep=s->step;
    p->lifeSteps=(uint32_t)((e->lifeMinUs+(uint64_t)((e->lifeMaxUs-e->lifeMinUs)*nrRandom(e->seed,ordinal,3)))*120/1000000);
    if(!p->lifeSteps)p->lifeSteps=1;
    p->state=1;
    p->effect=e->effect;
    p->material=e->material;nrHeatSpawn(s,slot);
    p->size=e->sizeMin+(e->sizeMax-e->sizeMin)*nrRandom(e->seed,ordinal,4);
    p->angle=nrRandom(e->seed,ordinal,5)*360;
    double sw=e->shapeWeights.x+e->shapeWeights.y+e->shapeWeights.z;
    double pick=nrRandom(e->seed,ordinal,50)*sw;
    p->leafShape=pick<e->shapeWeights.x?0:pick<e->shapeWeights.x+e->shapeWeights.y?1:2;
    Vec3 local=nrV(randomSigned(e->seed,ordinal,6)*e->extent.x*.5,randomSigned(e->seed,ordinal,7)*e->extent.y*.5,randomSigned(e->seed,ordinal,8)*e->extent.z*.5);
    if(e->shape%5==0)local=nrV(0,0,0);
    if(e->shape%5==2) {
        Vec3 d=randomUnit(e->seed,ordinal);
        double r=nrRandom(e->seed,ordinal,9);
        local=nrV(d.x*e->extent.x*.5*r,d.y*e->extent.y*.5*r,d.z*e->extent.z*.5*r);
    }
    if(e->shape==7) {
        /* Uniform ellipsoid volume: uniform azimuth and z, radius CDF r^3.
         * Fixed bisection avoids platform libm/cbrt in native and WASM. */
        double z=randomSigned(e->seed,ordinal,100);
        double theta=nrRandom(e->seed,ordinal,101)*360;
        double radial=nrSqrt(1-z*z),u=nrRandom(e->seed,ordinal,9);
        double lo=0,hi=1;
        for(int k=0;k<32;k++) {double mid=(lo+hi)*.5;if(mid*mid*mid<u)lo=mid;else hi=mid;}
        double radius=(lo+hi)*.5;
        local=nrV(radial*nrCos(theta)*e->extent.x*.5*radius,
                  z*e->extent.y*.5*radius,
                  radial*nrSin(theta)*e->extent.z*.5*radius);
    }
    if(e->shape%5==3)local=nrV(nrCos(p->angle)*e->extent.x*.5*nrSqrt(nrRandom(e->seed,ordinal,10)),0,nrSin(p->angle)*e->extent.z*.5*nrSqrt(nrRandom(e->seed,ordinal,10)));
    if(e->shape%5==4)local=nrScale(e->extent,randomSigned(e->seed,ordinal,11)*.5);
    Vec3 pos=nrAdd(e->position,local),vel=nrAdd(e->velocity,nrV(e->spread.x*randomSigned(e->seed,ordinal,12),e->spread.y*randomSigned(e->seed,ordinal,13),e->spread.z*randomSigned(e->seed,ordinal,14)));
    int a=nrEffectAlgorithm(e->effect);
    if(a==4||a==5) {
        Vec3 authoredVelocity=vel;
        Vec3 direction=randomUnit(e->seed,ordinal);
        if(e->topology==1)direction=nrV(nrCos(p->angle),nrSin(p->angle),.02*randomSigned(e->seed,ordinal,15));
        if(e->topology==2)direction=nrNormal(nrV(direction.x,.6+nrAbs(direction.y),direction.z));
        if(e->topology==3)direction=nrNormal(nrV(nrCos((ordinal%8)*45),.7,nrSin((ordinal%8)*45)));
        if(e->topology==4)direction=nrNormal(nrV(direction.x,.7+.7*nrAbs(direction.y),direction.z));
        if(e->topology==5) {
            int count=e->count>0?e->count:64,index=ordinal%count;
            double y=1-2*(index+.5)/count,azimuth=index*137.50776405003785+nrRandom(e->seed,0,17)*360;
            double radial=nrSqrt(1-y*y);direction=nrV(radial*nrCos(azimuth),y,radial*nrSin(azimuth));
        }
        double speed=e->radius*(a==5?1.25:1.8)*(.65+.35*nrRandom(e->seed,ordinal,16));
        if(e->topology==4)speed*=.65;
        vel=nrAdd(vel,nrScale(direction,speed));
        pos=e->position;
        if(a==5&&e->topology==5&&(nrEffectProfile(e->effect)==1||nrEffectProfile(e->effect)==2)){
            int count=e->count>0?e->count:64,index=ordinal%count;
            double y=1-2*(index+.5)/count,angle=index*137.50776405003785+e->seed*.0001*57.29577951308232;
            double radial=nrSqrt(1-y*y),variation=1;
            if(nrEffectProfile(e->effect)==1)variation+=.13*nrSin(angle*3+(y*8+e->seed)*57.29577951308232);
            direction=nrV(nrCos(angle)*radial,y,nrSin(angle)*radial);
            pos=nrAdd(e->position,nrScale(direction,e->radius*variation));
            vel=nrAdd(authoredVelocity,nrScale(direction,e->radius*variation*4.2));
            if(nrEffectProfile(e->effect)==1)s->novaOptics[slot]=(NovaOptics){1,e->seed,(uint32_t)count,(uint32_t)index};
        }
    }
    Vec3 orientation=s->birthOrientations[ei];
    if(orientation.x||orientation.y||orientation.z) {
        pos=nrAdd(e->position,birthTransform(nrSub(pos,e->position),orientation));
        vel=birthTransform(vel,orientation);
    }
    p->position=nrQuantize(pos);
    p->previous=p->position;
    p->velocity=nrQuantize(vel);
    p->heat=1;
    s->births++;
}
static void depositRejected(State*s,int surfaceId) {
    s->depositsRejected++;
    if(surfaceId)s->geometry.surfaces[surfaceId-1].rejectedDeposits++;
}
static void rememberContact(SurfaceContact*out,const GeometryHit*hit) {
    /* Explicitly clear ABI padding: canonical snapshots compare C/WASM bytes. */
    memset(out,0,sizeof(*out));out->used=1;out->surfaceId=hit->surfaceId;
    out->triangleIndex=hit->triangleIndex;out->normal=hit->normal;
}
static void deposit(State*s,Particle*p,const GeometryHit*hit) {
    nrSurfaceWaterImpact(s,(int)(p-s->particles),hit);
    nrFlowSprayRelease(s,(int)(p-s->particles),1);
    Floor*f=&s->floor;
    int surfaceId=hit?hit->surfaceId:0;
    Surface*surface=surfaceId?&s->geometry.surfaces[surfaceId-1]:0;
    int maxIndividual=surface?surface->maxIndividual:f->maxIndividual;
    int maxTiles=surface?surface->maxTiles:f->maxTiles;
    int overflow=surface?surface->overflow:f->overflow;
    int count=0,slot=-1;
    for(int i=0;i<NR_DEPOSITS;i++) {
        if(s->deposits[i].used&&s->geometry.depositContacts[i].surfaceId==surfaceId)count++;
        if(!s->deposits[i].used&&slot<0)slot=i;
    }
    if(count<maxIndividual&&slot>=0) {
        Deposit*d=&s->deposits[slot];
        memset(d,0,sizeof(*d));memset(&s->geometry.depositContacts[slot],0,sizeof(SurfaceContact));
        d->used=1;d->id=p->id;d->seed=p->seed;d->effect=p->effect;d->material=p->material;
        d->position=nrUnquantize(p->position);
        if(surfaceId) {
            d->position=nrAdd(hit->position,nrScale(hit->normal,.02));
            rememberContact(&s->geometry.depositContacts[slot],hit);
        } else d->position.y=f->height+.02;
        d->size=p->size;d->angle=p->angle;d->alpha=.7;
        d->atUs=s->timeUs;d->emitterId=p->emitterId;d->emitterGeneration=s->emitters[p->emitterSlot].generation;d->leafShape=p->leafShape;
        nrHeatDeposit(s,(int)(p-s->particles),1,slot);
        d->sampling=s->emitters[p->emitterSlot].sampling;d->surfaceAlpha=s->emitters[p->emitterSlot].surfaceAlpha;
        const Emitter*e=&s->emitters[p->emitterSlot];
        d->veinContrast=e->veinContrast;d->curl=e->curl;d->backTint=e->backTint;
    } else if(overflow==1) {
        Vec3 pos=nrUnquantize(p->position);
        int x=surfaceId?0:(int)nrFloor(pos.x/f->cellSize);
        int z=surfaceId?0:(int)nrFloor(pos.z/f->cellSize),free=-1,n=0;
        for(int i=0;i<NR_TILES;i++) {
            DepositTile*t=&s->tiles[i];SurfaceTile*geometry=&s->geometry.tileSurfaces[i];
            if(t->used) {
                if(geometry->surfaceId!=surfaceId)continue;
                n++;
                int same=surfaceId?geometry->triangleIndex==hit->triangleIndex&&
                    geometry->meshGeneration==s->geometry.meshGeneration&&nrDot(geometry->normal,hit->normal)>.999999:
                    t->x==x&&t->z==z;
                if(same&&t->emitterId==p->emitterId&&nrAggregateCompatible(s,i,(int)(p-s->particles))) {
                    if(t->count==0xffffffffu)depositRejected(s,surfaceId);
                    else {t->count++;t->atUs=s->timeUs;s->aggregateCount++;nrHeatDeposit(s,(int)(p-s->particles),2,i);}
                    nrFlowSprayRelease(s,(int)(p-s->particles),0);p->state=0;return;
                }
            } else if(free<0)free=i;
        }
        if(n<maxTiles&&free>=0) {
            double alpha;DepositTile*t=&s->tiles[free];
            *t=(DepositTile){1,x,z,1,nrPaint(s,p->material,s->timeUs,p->id,&alpha),p->emitterId,s->timeUs};
            SurfaceTile*geometry=&s->geometry.tileSurfaces[free];memset(geometry,0,sizeof(*geometry));
            if(surfaceId) {
                Triangle sampled=s->mesh[hit->triangleIndex];nrDisplaceSurfaceTriangle(s,hit->triangleIndex,&sampled);const Triangle*triangle=&sampled;Vec3 offset=nrScale(hit->normal,.008);
                geometry->surfaceId=surfaceId;geometry->triangleIndex=hit->triangleIndex;
                geometry->meshGeneration=s->geometry.meshGeneration;geometry->normal=hit->normal;
                geometry->a=nrAdd(triangle->a,offset);geometry->b=nrAdd(triangle->b,offset);geometry->c=nrAdd(triangle->c,offset);
            }
            nrAggregateCapture(s,free,(int)(p-s->particles));nrHeatDeposit(s,(int)(p-s->particles),2,free);s->aggregateCount++;
        } else depositRejected(s,surfaceId);
    } else depositRejected(s,surfaceId);
    nrFlowSprayRelease(s,(int)(p-s->particles),0);p->state=0;
}
/* At most four contacts resolve one explicit 1/120 second step. The full segment
 * is tested before response, and remaining time continues with the reflected
 * velocity. No camera, render count or allocation order enters this query. */
static int surfaceMotion(State*s,int slot,Vec3 from,Vec3*position,Vec3*velocity,int algorithm,uint32_t age) {
    Particle*p=&s->particles[slot];Emitter*e=&s->emitters[p->emitterSlot];
    uint32_t mask=nrEmitterColliderMask(s,p->emitterSlot);
    double remaining=1.0/120;Vec3 current=from,v=*velocity;
    for(int contact=0;contact<NR_COLLISION_CONTACTS;contact++) {
        Vec3 target=nrAdd(current,nrScale(v,remaining));GeometryHit hit;uint32_t tested=0;
        s->geometry.collisionQueries++;
        double start=(s->step-1)/120.0+(1.0/120-remaining);
        int found=nrGeometryHitTimed(s,mask,current,target,start,remaining,&hit,&tested);
        if(found<0)return -1;
        s->geometry.triangleTests+=tested;
        if(!found){*position=target;*velocity=v;return 0;}
        Surface*surface=hit.surfaceId?&s->geometry.surfaces[hit.surfaceId-1]:0;
        current=nrAdd(hit.position,nrScale(hit.normal,.001));
        rememberContact(&s->geometry.particleContacts[slot],&hit);
        if(!nrHeatContact(s,slot,&hit))return -1;
        nrSurfaceImpact(s,hit.surfaceId,p,algorithm);
        nrFoamImpact(s,&hit,p,v);
        if(algorithm==1) {
            nrSurfaceWaterImpact(s,slot,&hit);
            nrFlowSprayRelease(s,slot,1);
            if(!surface)s->floor.wetness=nrClamp(s->floor.wetness+p->size*.03,0,1);
            p->position=nrQuantize(current);p->state=2;p->bornStep=s->step;p->lifeSteps=72;
            p->velocity=nrQuantize(nrV(0,0,0));p->effect=nrEffectId("weather/pressure-shell");
            return 1;
        }
        Vec3 relative=nrSub(v,hit.surfaceVelocity);
        double normalSpeed=nrDot(relative,hit.normal);
        double settleSpeed=surface?surface->settleSpeed:s->floor.settleSpeed;
        if(e->deposit&&(nrAbs(normalSpeed)<settleSpeed+1||age>120||algorithm==2||algorithm==0)) {
            p->position=nrQuantize(current);deposit(s,p,&hit);return 1;
        }
        if(normalSpeed<0) {
            double restitution=surface?surface->restitution:s->floor.restitution;
            double friction=surface?surface->friction:s->floor.friction;
            Vec3 tangent=nrSub(relative,nrScale(hit.normal,normalSpeed));
            v=nrAdd(hit.surfaceVelocity,nrSub(nrScale(tangent,1-friction),nrScale(hit.normal,normalSpeed*restitution)));
        }
        remaining*=1-hit.fraction;
        if(remaining<=1e-12){*position=current;*velocity=v;return 0;}
    }
    s->geometry.contactBudgetExhausted++;
    *position=current;*velocity=v;return 0;
}
static Vec3 windAt(const Emitter*e,Vec3 pos,double time) {
    double phase=(pos.x+pos.z*.63)/e->windScale*180+time/e->windPeriod*360;
    return nrAdd(e->wind,nrV(nrSin(phase)*e->windVariation.x,nrSin(phase*.73+91)*e->windVariation.y,nrSin(phase*.87-37)*e->windVariation.z));
}
/* Schedules are monotone by ordinal, including jitter confined to each birth's
 * interval. Search the due prefix without iterating rejected births. */
static int birthDue(const Emitter*q,int ordinal,uint64_t time) {
    if(time<q->startUs)return 0;
    if(q->rate>0) {
        uint64_t cutoff=time;
        if(q->runningUs&&cutoff>q->startUs+q->runningUs)cutoff=q->startUs+q->runningUs;
        double offset=(ordinal+1)*1000000.0/q->rate;
        /* floor(offset)<=cutoff-start. Compare before converting: very small
         * positive rates can produce offsets outside uint64 and scene time. */
        return offset<(double)(cutoff-q->startUs)+1;
    }
    int within=q->count?ordinal%q->count:0,cycle=q->count?ordinal/q->count:0;
    uint64_t birth=q->startUs+(q->runningUs+q->gapUs)*(uint64_t)cycle;
    if(q->runningUs) {
        double fraction=(within+(q->schedule?nrRandom(q->seed,ordinal,80):0))/(double)(q->count?q->count:1);
        birth+=(uint64_t)(fraction*q->runningUs);
    }
    return birth<=time;
}
static int duePrefix(const Emitter*q,int limit,uint64_t time) {
    int low=q->born,high=limit;
    if(low>=high||!birthDue(q,low,time))return low;
    while(low<high) {
        int middle=low+(high-low)/2;
        if(birthDue(q,middle,time))low=middle+1;else high=middle;
    }
    return low;
}
int nrSimulate(State*s) {
    if(!nrHeatTick(s))return 0;
    double dt=1.0/120.0,now=s->timeUs/1e6;
    int nextSlot=0;
    for(int e=0; e<(int)NR_MAX_EMITTERS; e++) {
        Emitter*q=&s->emitters[e];
        if(!q->used||q->stopping||s->timeUs<q->startUs)continue;
        /* Birth schedule depends only on clock, emitter key and ordinal. The
         * rate case starts after its first complete interval; finite burst starts
         * at the first simulation boundary. Repeated births never reuse IDs. */
        int limit=q->rate>0?1000000000:q->count*q->cycles;
        int flowDriven=s->flowSprays[e].flowId!=0;
        int due=flowDriven?nrFlowSprayDue(s,e):duePrefix(q,limit,s->timeUs);
        while(q->born<due) {
            if(s->nextParticle==0xffffffffu) {
                if(!flowDriven){s->rejectedBirths+=(uint64_t)(due-q->born);q->born=due;}break;
            }
            /* No slots are freed during this birth phase. A forward cursor
             * preserves the original lowest-free-slot ordering across emitters. */
            while(nextSlot<(int)NR_MAX_PARTICLES&&s->particles[nextSlot].state)nextSlot++;
            if(nextSlot==(int)NR_MAX_PARTICLES) {
                if(!flowDriven){s->rejectedBirths+=(uint64_t)(due-q->born);q->born=due;}break;
            }
            spawn(s,e,q->born,nextSlot++);q->born++;
            if(flowDriven){s->flowSprays[e].ordinal=q->born;s->flowSprays[e].emittedVolume=q->born*s->flowSprays[e].particleVolume;}
        }
        uint64_t end=q->startUs+(q->runningUs+q->gapUs)*(uint64_t)(q->cycles-1)+q->runningUs;
        if(!flowDriven&&q->endStyle!=0&&(q->rate==0||q->runningUs>0)&&s->timeUs>=end) {
            q->stopping=1;q->stopUs=end;
        }
    }
    s->floor.wetness=nrClamp(s->floor.wetness-s->floor.evaporation*dt,0,1);
    nrSurfaceTick(s);
    if(!nrSurfaceWaterTransport(s))return 0;

    for(int i=0; i<(int)NR_MAX_PARTICLES; i++) {
        Particle*p=&s->particles[i];
        if(!p->state)continue;
        Emitter*e=&s->emitters[p->emitterSlot];
        uint32_t age=s->step-p->bornStep;
        if(age>=p->lifeSteps) {
            nrFlowSprayRelease(s,(int)(p-s->particles),0);p->state=0;
            s->expired++;
            continue;
        }
        if(e->stopping&&e->endStyle!=0&&s->timeUs-e->stopUs>=e->tailUs) {
            nrFlowSprayRelease(s,(int)(p-s->particles),0);p->state=0;s->expired++;continue;
        }
        if(p->state==2)continue;
        p->previous=p->position;
        Vec3 pos=nrUnquantize(p->position),v=nrUnquantize(p->velocity);
        double ageSec=age/120.0;
        Vec3 wind=windAt(e,pos,now),acc=nrAdd(e->gravity,nrScale(nrSub(wind,v),e->drag));
        int a=nrEffectAlgorithm(e->effect);
        if(a==0||a==2) {
            double phase=p->angle+ageSec*e->flutterHz*360;
            acc.x+=nrSin(phase)*e->flutterAmount;
            acc.z+=nrCos(phase*.73)*e->flutterAmount;
            acc.y+=e->lift*nrAbs(nrSin(phase*.37));
        }
        if(a==3) {
            double h=nrClamp((pos.y-e->position.y)/e->radius,0,1);
            double radius=nrSqrt((pos.x-e->position.x)*(pos.x-e->position.x)+(pos.z-e->position.z)*(pos.z-e->position.z));
            if(!(e->stopping&&e->endStyle==4)) {
                acc.y+=e->heat*(1-h)*nrClamp(1-radius/e->radius,0,1);
                p->heat=nrClamp(1-ageSec/(p->lifeSteps/120.0),0,1);
            }
        }
        if(a==6) {
            v=nrV(0,0,0);
            acc=nrV(0,0,0);
        }
        if(e->stopping) {
            double tail=(s->timeUs-e->stopUs)/1e6;
            if(e->endStyle==4)p->heat=nrClamp(p->heat-dt/(e->tailUs?e->tailUs/1e6:dt),0,1);
            if(e->endStyle!=0&&s->timeUs-e->stopUs>=e->tailUs) {
                nrFlowSprayRelease(s,(int)(p-s->particles),0);p->state=0;s->expired++;continue;
            }
            if(e->endStyle==2||e->endStyle==4) {
                if(s->timeUs-e->stopUs>=e->tailUs) {
                    nrFlowSprayRelease(s,(int)(p-s->particles),0);p->state=0;
                    continue;
                }
            }
            else if(e->endStyle==1)acc.y-=10;
            else if(e->endStyle==3)acc=nrAdd(acc,nrV(18,3,10));
            else if(e->endStyle==5&&tail<.5)acc=nrAdd(acc,nrScale(randomUnit(p->seed,1),60));
        }
        v=nrAdd(v,nrScale(acc,dt));
        Vec3 from=pos;pos=nrAdd(pos,nrScale(v,dt));
        uint32_t colliderMask=nrEmitterColliderMask(s,p->emitterSlot);
        int meshCollision=e->collision&&(colliderMask&~1u);
        if(meshCollision){int result=surfaceMotion(s,i,from,&pos,&v,a,age);if(result<0)return 0;if(result)continue;}
        if(nrAbs(pos.x)>16000||nrAbs(pos.y)>16000||nrAbs(pos.z)>16000) {
            nrFlowSprayRelease(s,i,2);
            nrFlowSprayRelease(s,(int)(p-s->particles),0);p->state=0;
            s->expired++;
            continue;
        }
        if(!meshCollision&&(colliderMask&1u)&&s->floor.enabled&&e->collision&&pos.y<=s->floor.height) {
            pos.y=s->floor.height+.001;
            if(a==1) {
                nrFlowSprayRelease(s,i,1);
                /* Impacts are spatial and retained briefly, never screen-random. */
                s->floor.wetness=nrClamp(s->floor.wetness+p->size*.03,0,1);
                p->position=nrQuantize(pos);
                p->state=2;
                p->bornStep=s->step;
                p->lifeSteps=72;
                p->velocity=nrQuantize(nrV(0,0,0));
                p->effect=nrEffectId("weather/pressure-shell");
                continue;
            }
            if(e->deposit&&(nrAbs(v.y)<s->floor.settleSpeed+1||age>120||a==2||a==0)) {
                p->position=nrQuantize(pos);
                deposit(s,p,0);
                continue;
            }
            v.y=nrAbs(v.y)*s->floor.restitution;
            v.x*=1-s->floor.friction;
            v.z*=1-s->floor.friction;
        }
        p->position=nrQuantize(pos);
        p->velocity=nrQuantize(v);
    }
    for(int i=0; i<NR_DEPOSITS; i++) {
        Deposit*d=&s->deposits[i];
        if(!d->used)continue;
        const SurfaceContact*contact=&s->geometry.depositContacts[i];
        const Surface*surface=contact->surfaceId?&s->geometry.surfaces[contact->surfaceId-1]:0;
        uint64_t retention=surface?surface->retentionUs:s->floor.retentionUs;
        double reentrain=surface?surface->reentrain:s->floor.reentrain;
        Vec3 normal=surface?contact->normal:nrV(0,1,0);
        if(retention&&s->timeUs-d->atUs>=retention) {
            nrHeatRelease(s,1,i);d->used=0;
            continue;
        }
        /* Re-entrainment belongs to the depositing emitter, not the first leaf
         * emitter in an array. Removed emitters cannot commandeer old deposits.
         * A destructive ending owns no future airborne matter: lifting its
         * deposits would expire them at its tail, so they keep receiver clocks. */
        int ei=nrFindEmitter(s,(int)d->emitterId);
        if(ei>=0&&s->emitters[ei].generation==d->emitterGeneration&&!(s->emitters[ei].stopping&&s->emitters[ei].endStyle!=0)&&reentrain>0&&s->step%24==(uint32_t)i%24) {
            Emitter*e=&s->emitters[ei];
            Vec3 w=windAt(e,d->position,now);
            Vec3 tangent=nrSub(w,nrScale(normal,nrDot(w,normal)));
            if(nrSqrt(nrDot(tangent,tangent))>reentrain) {
                int slot=allocate(s);
                if(slot>=0) {
                    Particle*p=&s->particles[slot];
                    memset(p,0,sizeof(*p));
                    memcpy(&s->particleMotions[slot],&s->emitterMotions[ei],sizeof(s->particleMotions[slot]));
                    memset(&s->geometry.particleContacts[slot],0,sizeof(SurfaceContact));
                    p->id=d->id;
                    p->emitterId=e->id;
                    p->emitterSlot=ei;
                    p->seed=d->seed;
                    p->bornStep=s->step;
                    p->lifeSteps=1800;
                    p->state=1;
                    p->effect=d->effect;
                    p->material=d->material;
                    p->position=nrQuantize(nrAdd(d->position,nrScale(normal,.15)));
                    p->previous=p->position;
                    p->velocity=nrQuantize(nrAdd(w,nrScale(normal,3)));
                    p->size=d->size;
                    p->angle=d->angle;p->leafShape=d->leafShape;
                    nrHeatReentrain(s,i,slot);d->used=0;
                }
            }
        }
    }
    for(int i=0;i<NR_TILES;i++)if(s->tiles[i].used) {
        int surfaceId=s->geometry.tileSurfaces[i].surfaceId;
        uint64_t retention=surfaceId?s->geometry.surfaces[surfaceId-1].retentionUs:s->floor.retentionUs;
        if(retention&&s->timeUs-s->tiles[i].atUs>=retention){nrHeatRelease(s,2,i);s->tiles[i].used=0;}
    }
    for(int i=0; i<NR_FIELDS; i++)if(s->fields[i].used&&!s->fieldControls[i].continuous&&s->timeUs-s->fields[i].atUs>=s->fields[i].lifeUs){s->fields[i].used=0;memset(&s->fieldControls[i],0,sizeof(s->fieldControls[i]));}
    nrStatusTick(s);
    return 1;
}
int nrParticlePose(const State*s,int i,Vec3*orientation,Vec3*angular) {
    if(i<0||i>=(int)NR_MAX_PARTICLES||!s->particles[i].state||!s->particleMotions[i].authored)return 0;
    *angular=s->particleMotions[i].angularVelocity;
    double age=(s->step-s->particles[i].bornStep)/120.0;
    *orientation=nrAdd(s->particleMotions[i].orientation,nrScale(*angular,age));return 1;
}
static Vec3 leafVertex(Vec3 center,double x,double y,double size,double yaw,double roll,double pitch,double curl,const Vec3*surfaceNormal,const Vec3*orientation) {
    Vec3 v=nrV(x*size,y*size,curl*x*x*size);
    if(orientation)return nrAdd(center,birthTransform(v,*orientation));
    double X=v.x*nrCos(yaw)-v.y*nrSin(yaw),Y=v.x*nrSin(yaw)+v.y*nrCos(yaw);
    v=nrV(X,Y*nrCos(roll)-v.z*nrSin(roll),Y*nrSin(roll)+v.z*nrCos(roll));
    v=nrV(v.x*nrCos(pitch)+v.z*nrSin(pitch),v.y,-v.x*nrSin(pitch)+v.z*nrCos(pitch));
    if(surfaceNormal) {
        Vec3 tangent,bitangent;nrSurfaceBasis(*surfaceNormal,&tangent,&bitangent);
        v=nrAdd(nrAdd(nrScale(tangent,v.x),nrScale(bitangent,v.y)),nrScale(*surfaceNormal,v.z));
    }
    return nrAdd(center,v);
}
static void drawLeaf(NrContext*c,const Projection*proj,Vec3 pos,double size,double yaw,double roll,double pitch,uint32_t color,double alpha,int shape,double vein,double curl,double backTint,int twoSided,double surfaceAlpha,const Vec3*surfaceNormal,const Vec3*orientation) {
    Vec3 previous={0};
    const int sampling=c->paintSampling;
    Vec3 authoredNormal=orientation?birthTransform(nrV(0,0,1),*orientation):nrV(0,0,1);
    if(surfaceNormal?nrDot(*surfaceNormal,nrSub(proj->position,pos))<0:orientation?nrDot(authoredNormal,nrSub(proj->position,pos))<0:nrCos(roll)*nrCos(pitch)<0) {
        if(!twoSided)return;
        color=nrMix(color,0xbcaa7c,backTint);
    }
    for(int k=0;k<=32;k++) {
        double a=k*360.0/32,lobe=shape==1?(.8+.28*nrCos(a*5)):1;
        /* Ovate silhouette lifts the supplied tumbling-outline equation into
         * oriented geometry; maple/lanceolate remain authored shape choices. */
        double x=nrSin(a)*.48*nrSin(a*.5)*lobe,y=nrCos(a);
        if(shape==2)x*=.42;
        Vec3 v=leafVertex(pos,x,y,size,yaw,roll,pitch,curl,surfaceNormal,orientation);
        if(k) {
            c->paintDetail=1;c->paintSampling=sampling;
            nrLine(c,proj,previous,v,color,alpha);
            Triangle t= {
                pos,previous,v,nrMix(color,0x221712,.4),alpha*surfaceAlpha
            };
            /* A braille blade is foreground geometry, not a solid cell matte.
             * Keep its role separate from the outline/veins so their masks survive. */
            c->paintDetail=sampling==2?2:0;c->paintSampling=sampling==2?2:0;
            nrTriangle(c,proj,t);
        }
        previous=v;
    }
    c->paintDetail=1;c->paintSampling=sampling;
    nrLine(c,proj,leafVertex(pos,0,-1.3,size,yaw,roll,pitch,curl,surfaceNormal,orientation),leafVertex(pos,0,.85,size,yaw,roll,pitch,curl,surfaceNormal,orientation),nrMix(color,0xdfcd9c,.2),alpha);
    for(int k=0; k<3; k++) {
        double y=-.4+k*.45;
        for(int sign=-1; sign<=1; sign+=2)nrLine(c,proj,leafVertex(pos,0,y-.16,size,yaw,roll,pitch,curl,surfaceNormal,orientation),leafVertex(pos,sign*.3,y+.08,size,yaw,roll,pitch,curl,surfaceNormal,orientation),color,alpha*vein);
    }
}
void nrDrawWeather(NrContext*c,const Projection*proj) {
    const State*s=nrView(c);
    for(int i=0; i<(int)NR_MAX_PARTICLES; i++) {
        const Particle*p=&s->particles[i];
        if(!p->state)continue;
        const Emitter*e=&s->emitters[p->emitterSlot];
        if(s->studioNovaControls[p->emitterSlot].used||s->worldSourceControls[p->emitterSlot].used||s->thermalSourceControls[p->emitterSlot].used||s->atelierControls[p->emitterSlot].used||s->observatoryControls[p->emitterSlot].used||s->kineticControls[p->emitterSlot].used)continue; /* Source profile replaces appearance, not physics. */
        double age=(s->step-p->bornStep)/120.0,life=p->lifeSteps/120.0;
        double fade=nrClamp(age/(e->birthFadeUs/1e6+.001),0,1)*nrClamp((life-age)/(e->deathFadeUs/1e6+.001),0,1)*e->alpha;
        if(e->stopping&&e->endStyle==2)fade*=1-nrClamp((double)(s->timeUs-e->stopUs)/(e->tailUs?e->tailUs:1),0,1);
        double ma;
        nrUseMaterial(c,p->material);
        /* Hybrid weather is a braille object, leaf blade included (MIXED-LAYERS.md). */
        c->paintOwner=0x20000000u|(uint32_t)(i+1);c->paintDetail=1;c->paintSampling=nrDictatedSampling(e->sampling,2);
        uint32_t color=nrPaint(s,p->material,s->timeUs,p->id,&ma);
        fade*=ma;
        double nova[4];
        if(nrNovaAppearance(s,i,nova)){
            double physicalAge=nova[0]/1000000.0;
            double birth=e->birthFadeUs?nrClamp(physicalAge/(e->birthFadeUs/1000000.0),0,1):1;
            double death=e->deathFadeUs?nrClamp((life-physicalAge)/(e->deathFadeUs/1000000.0),0,1):1;
            fade=e->alpha*ma*nova[2]*birth*death;
            if(e->stopping&&e->endStyle==2)fade*=1-nrClamp((double)(s->timeUs-e->stopUs)/(e->tailUs?e->tailUs:1),0,1);
            color=nrColorWithHue(color,nova[3]);
        }
        if(e->stopping&&e->endStyle==4)fade*=p->heat;
        Vec3 pos=nrUnquantize(p->position),velocity=nrUnquantize(p->velocity);
        int a=nrEffectAlgorithm(p->effect);
        double distance=nrSqrt(nrDot(nrSub(pos,proj->position),nrSub(pos,proj->position)));
        if(distance<e->nearDistance||distance>e->farDistance)continue;
        if(e->farFade>0)fade*=nrClamp((e->farDistance-distance)/e->farFade,0,1);
        uint32_t previousPattern=c->paintMaterialId;c->paintMaterialId=s->materialPatterns[p->material].used?(uint32_t)p->material+1:0;
        if(p->state==2) {
            double radius=age*3;
            const SurfaceContact*contact=&s->geometry.particleContacts[i];
            Vec3 tangent=nrV(1,0,0),bitangent=nrV(0,0,1),normal=nrV(0,1,0);
            if(contact->used&&contact->surfaceId) {
                normal=contact->normal;nrSurfaceBasis(normal,&tangent,&bitangent);
            }
            for(int k=0; k<18; k++) {
                Vec3 offset=nrAdd(pos,nrScale(normal,.035));
                Vec3 u=nrAdd(offset,nrAdd(nrScale(tangent,nrCos(k*20)*radius),nrScale(bitangent,nrSin(k*20)*radius)));
                Vec3 v=nrAdd(offset,nrAdd(nrScale(tangent,nrCos((k+1)*20)*radius),nrScale(bitangent,nrSin((k+1)*20)*radius)));
                nrLine(c,proj,u,v,color,fade*.45);
            }
            c->paintMaterialId=previousPattern;
            continue;
        }
        Vec3 pose,angular;int authored=nrParticlePose(s,i,&pose,&angular);
        if(a==0)drawLeaf(c,proj,pos,p->size,p->angle+age*e->tumble.y,nrSin(age*e->flutterHz*360+p->angle)*55+age*e->tumble.z,age*e->tumble.x,color,fade,p->leafShape,e->veinContrast,e->curl,e->backTint,e->twoSided,e->surfaceAlpha,0,authored?&pose:0);
        else if(a==1) {
            Vec3 previous=nrSub(pos,nrScale(velocity,e->trailUs/1e6));
            nrLine(c,proj,previous,pos,nrMix(color,0xaedbea,.3),fade*.7);
            nrPoint(c,proj,pos,color,fade,p->size);
        }
        else if(a==2) {
            double spin=age*e->tumble.y+p->angle;
            for(int k=0; k<3; k++) {
                double an=spin+k*60;
                Vec3 tip=nrV(nrCos(an)*p->size,nrSin(an)*p->size, nrSin(spin*.7)*p->size*.4);
                if(authored)tip=birthTransform(nrV(nrCos(k*60)*p->size,nrSin(k*60)*p->size,0),pose);
                nrLine(c,proj,nrSub(pos,tip),nrAdd(pos,tip),nrMix(color,0xdbe9f1,.45),fade*.7);
            }
            nrPoint(c,proj,pos,color,fade,p->size*.1);
        }
        else if(a==6) {
            Vec3 end=nrAdd(e->position,nrScale(randomUnit(p->seed,1),e->radius*2));
            Vec3 start=pos,last=start;
            double phase=nrFloor(age*18);
            for(int k=1; k<=10; k++) {
                double u=k/10.0;
                Vec3 cur=nrAdd(start,nrScale(nrSub(end,start),u));
                double jitter=nrSin(u*180)*(.8+.3*nrSin(phase*97+p->angle));
                cur=nrAdd(cur,nrV(randomSigned(p->seed,k,(uint32_t)phase+5)*jitter,randomSigned(p->seed,k,(uint32_t)phase+8)*jitter,randomSigned(p->seed,k,13)*jitter));
                nrLine(c,proj,last,cur,nrMix(color,0xeef6ff,.55),fade*.8);
                if(k==4||k==7) {
                    Vec3 branch=nrAdd(cur,nrScale(randomUnit(p->seed,k),e->radius*.5));
                    nrLine(c,proj,cur,branch,color,fade*.5);
                }
                last=cur;
            }
        }
        else if(a==4) {
            double appearance[4];if(!nrBurstAppearance(s,i,appearance)){c->paintMaterialId=previousPattern;continue;}
            Vec3 previous=nrSub(pos,nrScale(velocity,e->trailUs/1e6));
            nrLine(c,proj,previous,pos,color,fade*appearance[2]*.55);
            nrPoint(c,proj,pos,color,fade*appearance[2],p->size);
            if(appearance[3]>0) {
                Vec3 delta=nrSub(pos,e->position);
                nrLine(c,proj,nrAdd(e->position,nrScale(delta,.15)),nrAdd(e->position,nrScale(delta,1.4)),nrMix(color,0xffffff,.7),fade*appearance[3]);
            }
        }
        else {
            if(a==3) {
                double h=e->stopping&&e->endStyle==4?p->heat:nrClamp(1-age/life,0,1);
                color=nrOklch((int32_t)((.3+.5*h)*1e6),(int32_t)(.09*1e6),(int32_t)((15+50*h)*1000));
                fade*=.35+.65*nrRandom(p->seed,(uint32_t)(age*14),0);
            }
            Vec3 trail=nrSub(pos,nrScale(velocity,e->trailUs/1e6));
            nrLine(c,proj,trail,pos,color,fade*.55);
            nrPoint(c,proj,pos,color,fade,p->size);
        }
        c->paintMaterialId=previousPattern;
    }
    /* One shared core per emitter, anchored to the brightest living burst.
     * Reuse that particle's actual hit owner; density cannot stack core alpha. */
    for(int ei=0;ei<(int)NR_MAX_EMITTERS;ei++)if(s->emitters[ei].used&&nrEffectAlgorithm(s->emitters[ei].effect)==4){
        const Emitter*e=&s->emitters[ei];if(s->studioNovaControls[ei].used||s->worldSourceControls[ei].used||s->thermalSourceControls[ei].used||s->atelierControls[ei].used||s->kineticControls[ei].used)continue;int best=-1;double core=0;
        for(int i=0;i<(int)NR_MAX_PARTICLES;i++)if(s->particles[i].emitterSlot==ei){double stage[4];if(nrBurstAppearance(s,i,stage)&&stage[1]>core){core=stage[1];best=i;}}
        if(best<0)continue;const Particle*p=&s->particles[best];double alpha;uint32_t color=nrPaint(s,p->material,s->timeUs,p->id,&alpha);
        alpha*=e->alpha*core;
        if(e->stopping&&e->endStyle==2)alpha*=1-nrClamp((double)(s->timeUs-e->stopUs)/(e->tailUs?e->tailUs:1),0,1);
        if(e->stopping&&e->endStyle==4)alpha*=p->heat;
        nrUseMaterial(c,p->material);c->paintOwner=0x20000000u|(uint32_t)(best+1);c->paintDetail=1;c->paintSampling=nrDictatedSampling(e->sampling,2);
        uint32_t previousPattern=c->paintMaterialId;c->paintMaterialId=s->materialPatterns[p->material].used?(uint32_t)p->material+1:0;
        nrPoint(c,proj,e->position,nrMix(color,0xffffff,.8),alpha,.5+e->radius*.15*core);c->paintMaterialId=previousPattern;
    }
    for(int i=0; i<NR_DEPOSITS; i++) {
        const Deposit*d=&s->deposits[i];
        if(!d->used)continue;
        double alpha;
        nrUseMaterial(c,d->material);
        c->paintOwner=0x30000000u|(uint32_t)(i+1);c->paintDetail=1;c->paintSampling=nrDictatedSampling(d->sampling,2);
        uint32_t color=nrPaint(s,d->material,s->timeUs,d->id,&alpha);
        int a=nrEffectAlgorithm(d->effect);
        const SurfaceContact*contact=&s->geometry.depositContacts[i];
        const Surface*surface=contact->surfaceId?&s->geometry.surfaces[contact->surfaceId-1]:0;
        uint64_t retention=surface?surface->retentionUs:s->floor.retentionUs,fade=surface?surface->fadeUs:s->floor.fadeUs;
        alpha*=depositFade(s->timeUs,d->atUs,retention,fade);
        uint32_t previousPattern=c->paintMaterialId;c->paintMaterialId=s->materialPatterns[d->material].used?(uint32_t)d->material+1:0;
        if(a==0) {
            /* The floor is a receiving surface too. The former 88-degree tilt
             * turned positive curl into negative height and buried the blade. */
            Vec3 normal=surface?contact->normal:nrV(0,1,0);
            drawLeaf(c,proj,d->position,d->size,d->angle,0,0,color,d->alpha*alpha,d->leafShape,d->veinContrast,d->curl,d->backTint,1,d->surfaceAlpha,&normal,0);
        }
        else nrPoint(c,proj,d->position,color,d->alpha*alpha,d->size);
        c->paintMaterialId=previousPattern;
    }
    c->paintBlend=0;c->paintOwner=3;c->paintDetail=0;c->paintSampling=nrDictatedSampling(s->floor.sampling,1);
    for(int i=0; i<NR_TILES; i++) {
        const DepositTile*t=&s->tiles[i];
        if(!t->used)continue;
        const SurfaceTile*surface=&s->geometry.tileSurfaces[i];
        const Surface*receiver=surface->surfaceId?&s->geometry.surfaces[surface->surfaceId-1]:0;
        double fade=depositFade(s->timeUs,t->atUs,receiver?receiver->retentionUs:s->floor.retentionUs,
                               receiver?receiver->fadeUs:s->floor.fadeUs);
        if(surface->surfaceId) {
            double alpha=nrClamp(t->count*.055,.08,.6)*fade;
            c->paintOwner=0x40010000u|(uint32_t)(i+1);c->paintSampling=nrDictatedSampling(s->meshSampling,1);
            nrTriangle(c,proj,(Triangle){surface->a,surface->b,surface->c,t->color,alpha});
            continue;
        }
        c->paintOwner=3;c->paintSampling=nrDictatedSampling(s->floor.sampling,1);
        double size=s->floor.cellSize,alpha=nrClamp(t->count*.055,.08,.6)*fade;
        Vec3 a=nrV(t->x*size,s->floor.height+.008,t->z*size),b=nrAdd(a,nrV(size,0,0)),d=nrAdd(a,nrV(0,0,size)),e=nrAdd(a,nrV(size,0,size));
        nrTriangle(c,proj,(Triangle) {
            a,b,e,t->color,alpha
        });
        nrTriangle(c,proj,(Triangle) {
            a,e,d,t->color,alpha
        });
    }
}
