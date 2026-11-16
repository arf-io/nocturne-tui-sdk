#include "internal.h"
/* Authored resource controls. Existing particles/identities and owned ledgers
 * are never reconstructed to apply a scalar change. */
static int duration(double x,uint64_t maximum,uint64_t*out){
    double us=x*1000;if(!(us>=0&&us<=maximum)||us!=(uint64_t)us)return 0;
    *out=(uint64_t)us;return 1;
}
static int component(const char*field,const char*name,Vec3*v,double x,double lo,double hi){
    size_t n=strlen(name);if(strncmp(field,name,n)||field[n]!='.'||!field[n+1]||field[n+2])return 0;
    if(!(x>=lo&&x<=hi))return -1;
    switch(field[n+1]){case 'x':v->x=x;break;case 'y':v->y=x;break;case 'z':v->z=x;break;default:return -1;}
    return 1;
}
int nrBindEmitterValue(State*s,const Value*v,double x){
    if(nrBurstBindingField(v->field))return nrBindBurstValue(s,v,x);
    int slot=nrFindEmitter(s,v->bindingId);if(slot<0)return 0;
    Emitter q=s->emitters[slot];int matched=0;
#define NUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;q.member=x;matched=1;}
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;q.member=(int)x;matched=1;}
#define VEC(name,member,lo,hi) {int r=component(v->field,name,&q.member,x,lo,hi);if(r<0)return 0;if(r)matched=1;}
    if(!strncmp(v->field,"position.",9))for(int i=0;i<16;i++)
        if(s->pathActors[i].used&&s->pathActors[i].family==1&&s->pathActors[i].targetId==q.id)return 0;
    VEC("position",position,-16000,16000) VEC("extent",extent,0,2000)
    VEC("velocity",velocity,-256,256) VEC("spread",spread,0,128)
    VEC("gravity",gravity,-256,256) VEC("wind",wind,-256,256)
    VEC("windVariation",windVariation,0,128) VEC("tumble",tumble,-720,720)
    VEC("shapeWeights",shapeWeights,0,1)
    NUM("windX",wind.x,-256,256) NUM("windY",wind.y,-256,256) NUM("windZ",wind.z,-256,256)
    NUM("alpha",alpha,0,1) NUM("heat",heat,0,64) NUM("drag",drag,0,30)
    NUM("lift",lift,0,20) NUM("flutterHz",flutterHz,0,30) NUM("flutterAmount",flutterAmount,0,10)
    NUM("sizeMin",sizeMin,.005,64) NUM("sizeMax",sizeMax,.005,64) NUM("radius",radius,.1,200)
    NUM("windScale",windScale,.1,1000) NUM("windPeriodSeconds",windPeriod,.1,120)
    NUM("nearDistance",nearDistance,.001,1000) NUM("farDistance",farDistance,.01,10000)
    NUM("farFadeDistance",farFade,0,10000) NUM("curl",curl,-2,2)
    if(!strcmp(v->field,"surfaceAlpha")||!strcmp(v->field,"veinContrast")||
       !strcmp(v->field,"backTint")||!strcmp(v->field,"twoSided")){
        if(nrEffectAlgorithm(q.effect)!=0)return 0;
        NUM("surfaceAlpha",surfaceAlpha,0,1) NUM("veinContrast",veinContrast,0,1)
        NUM("backTint",backTint,0,1) INT("twoSided",twoSided,0,1)
    }
    INT("sampling",sampling,0,3) INT("deposit",deposit,0,1) INT("collision",collision,0,1)
    INT("topology",topology,0,5)
    if(!strcmp(v->field,"material")){if(x<0||x>=NR_MATERIALS||x!=(int)x||!s->materials[(int)x].used)return 0;q.material=(int)x;matched=1;}
    int emission=!strcmp(v->field,"count")||!strcmp(v->field,"rate")||!strcmp(v->field,"cycles")||
        !strcmp(v->field,"gapMs")||!strcmp(v->field,"runningTimeMs");
    if(emission&&s->flowSprays[slot].flowId)return 0;
    INT("count",count,0,100000) NUM("rate",rate,0,10000) INT("cycles",cycles,1,10000)
#define DUR(name,member,maximum) if(!strcmp(v->field,name)){if(!duration(x,maximum,&q.member))return 0;matched=1;}
    DUR("runningTimeMs",runningUs,86400000000ull) DUR("gapMs",gapUs,60000000ull)
    DUR("lifetimeMinMs",lifeMinUs,3600000000ull) DUR("lifetimeMaxMs",lifeMaxUs,3600000000ull)
    DUR("tailMs",tailUs,3600000000ull)
#undef DUR
    const char*timings[]={"trailMs","birthFadeMs","deathFadeMs","coreMs"};
    uint32_t*timingTargets[]={&q.trailUs,&q.birthFadeUs,&q.deathFadeUs,&q.coreUs};
    const uint64_t limits[]={2000000,60000000,60000000,10000000};
    for(int i=0;i<4;i++)if(!strcmp(v->field,timings[i])){uint64_t us;if(!duration(x,limits[i],&us))return 0;*timingTargets[i]=(uint32_t)us;matched=1;}
    Vec3 birth=s->birthOrientations[slot],orientation=s->emitterMotions[slot].orientation,angular=s->emitterMotions[slot].angularVelocity;
    int b=component(v->field,"birthOrientation",&birth,x,-3600,3600);
    int o=component(v->field,"initialOrientation",&orientation,x,-3600,3600);
    int a=component(v->field,"angularVelocity",&angular,x,-720,720);
    if(b<0||o<0||a<0)return 0;
    if((o||a)&&nrEffectAlgorithm(q.effect)!=0&&nrEffectAlgorithm(q.effect)!=2)return 0;
    if(b||o||a)matched=1;
    if(!matched||q.sizeMin>q.sizeMax||q.nearDistance>=q.farDistance||q.farFade>q.farDistance-q.nearDistance||
       q.shapeWeights.x+q.shapeWeights.y+q.shapeWeights.z<=0||(q.deposit&&!q.collision)||
       q.lifeMinUs<1000||q.lifeMinUs>q.lifeMaxUs||(q.rate>0&&q.cycles!=1)||
       (!q.rate&&!s->flowSprays[slot].flowId&&q.born>q.count*q.cycles)||
       q.startUs+(q.runningUs+q.gapUs)*(uint64_t)(q.cycles-1)+q.runningUs>86400000000ull)return 0;
    s->emitters[slot]=q;s->birthOrientations[slot]=birth;
    if(o||a){s->emitterMotions[slot].orientation=orientation;s->emitterMotions[slot].angularVelocity=angular;s->emitterMotions[slot].authored=1;}
    return 1;
#undef NUM
#undef INT
#undef VEC
}

/* Validate a queued scalar's own domain without requiring the later host state
 * to retain its original effect, interval counterparts or allocation owners.
 * Only import scratch is touched, and every borrowed slot/sidecar is restored. */
int nrEmitterNumberValid(NrContext*c,State*s,const Value*v,double x){
    if(!c->checkingPending||s!=&c->probe||v->bindingFamily!=2||
       !nrResourceBindingShapeValid(v)||!nrValueNumberValid(v,x))return 0;
    int slot=nrFindEmitter(s,v->bindingId);if(slot<0)slot=0;
    BurstControls burst=s->burstControls[slot];
    Emitter saved=s->emitters[slot];Vec3 birth=s->birthOrientations[slot];
    unsigned char motion[sizeof(s->emitterMotions[0])],spray[sizeof(s->flowSprays[0])];int actors[16];
    memcpy(motion,&s->emitterMotions[slot],sizeof(motion));memcpy(spray,&s->flowSprays[slot],sizeof(spray));
    Emitter*q=&s->emitters[slot];q->used=1;q->id=v->bindingId;q->effect=nrEffectId(nrBurstBindingField(v->field)?"weather/chrysanthemum":"weather/autumn-drift");
    q->sizeMin=.005;q->sizeMax=64;q->nearDistance=.001;q->farDistance=10000;q->farFade=0;
    q->shapeWeights=nrV(1,1,1);q->collision=1;q->deposit=0;
    q->count=100000;q->born=0;q->rate=0;q->cycles=1;q->gapUs=q->runningUs=q->startUs=0;
    q->lifeMinUs=1000;q->lifeMaxUs=3600000000ull;
    memset(&s->flowSprays[slot],0,sizeof(s->flowSprays[slot]));
    for(int i=0;i<16;i++){
        actors[i]=s->pathActors[i].used;
        if(s->pathActors[i].family==1&&s->pathActors[i].targetId==(uint32_t)v->bindingId)s->pathActors[i].used=0;
    }
    int result=nrBindEmitterValue(s,v,x);
    for(int i=0;i<16;i++)s->pathActors[i].used=actors[i];
    s->burstControls[slot]=burst;s->emitters[slot]=saved;s->birthOrientations[slot]=birth;
    memcpy(&s->emitterMotions[slot],motion,sizeof(motion));memcpy(&s->flowSprays[slot],spray,sizeof(spray));
    return result;
}

int nrBindTextValue(State*s,const Value*v,double x){
    for(int i=0;i<NR_TEXTS;i++)if(s->text[i].used&&s->text[i].id==v->bindingId){
        TextRun*q=&s->text[i];
        if(!strcmp(v->field,"material")){if(x<0||x>=NR_MATERIALS||x!=(int)x||!s->materials[(int)x].used)return 0;q->material=(int)x;return 1;}
        TextRun old=*q;int matched=0;
#define NUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;q->member=x;matched=1;}
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;q->member=(int)x;matched=1;}
#define DUR(name,member,maximum) if(!strcmp(v->field,name)){if(!duration(x,maximum,&q->member))return 0;matched=1;}
        INT("x",x,NR_LAYOUT_MIN,NR_LAYOUT_MAX) INT("y",y,NR_LAYOUT_MIN,NR_LAYOUT_MAX)
        INT("width",width,1,NR_LAYOUT_MAX) INT("batchSize",batchSize,1,128)
        INT("local",local,0,1) INT("phase",phase,0,1) INT("easing",easing,0,9)
        INT("reverseOrder",reverseOrder,0,1) INT("randomOrder",randomOrder,0,1) INT("trailLength",trailLength,0,8)
        NUM("distance",distance,0,100) NUM("scatter",scatter,0,120) NUM("variation",variation,0,2)
        NUM("wind",wind,-100,100) NUM("overshoot",overshoot,0,3) NUM("cycles",cycles,0,50)
        NUM("scrambleHz",scrambleHz,0,120) NUM("hueSpread",hueSpread,-360,360)
        DUR("durationMs",durationUs,60000000) DUR("staggerMs",staggerUs,10000000)
        DUR("jitterMs",jitterUs,10000000) DUR("delayMs",delayUs,60000000)
        if(!matched)return 0;
        nrPrepareTextWithModels(q,s->textAlphabetTail[i],(int)s->textPhaseModel[i],&old,s->textAlphabetTail[i],(int)s->textPhaseModel[i],s->timeUs,&s->nextGlyphIdentity);return 1;
#undef NUM
#undef INT
#undef DUR
    }return 0;
}

int nrBindFloorValue(State*s,const Value*v,double x){
    if(v->bindingId)return 0;Floor q=s->floor;int matched=0;
#define NUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;q.member=x;matched=1;}
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;q.member=(int)x;matched=1;}
#define DUR(name,member,maximum) if(!strcmp(v->field,name)){if(!duration(x,maximum,&q.member))return 0;matched=1;}
    INT("enabled",enabled,0,1) INT("visible",visible,0,1) INT("sampling",sampling,0,3)
    INT("overflow",overflow,0,1) INT("maxIndividual",maxIndividual,0,NR_DEPOSITS) INT("maxTiles",maxTiles,0,NR_TILES)
    NUM("alpha",alpha,0,1) NUM("height",height,-1000,1000) NUM("restitution",restitution,0,1)
    NUM("friction",friction,0,1) NUM("settleSpeed",settleSpeed,0,30) NUM("reentrainWindSpeed",reentrain,0,256)
    NUM("cellSize",cellSize,.1,100) NUM("evaporation",evaporation,0,10)
    DUR("retentionMs",retentionUs,86400000000ull) DUR("fadeMs",fadeUs,60000000ull)
    if(!matched||(q.overflow==1&&!q.maxTiles)||(q.retentionUs&&q.fadeUs>q.retentionUs))return 0;
    s->floor=q;return 1;
#undef NUM
#undef INT
#undef DUR
}

int nrBindNodeValue(State*s,const Value*v,double x){
    int slot=nrFindNode(s,v->bindingId);if(slot<0)return 0;
    Node q=s->nodes[slot];int matched=0;
    if(!strncmp(v->field,"position.",9)){
        for(int i=0;i<16;i++)if(s->pathActors[i].used&&s->pathActors[i].family==3&&s->pathActors[i].targetId==(uint32_t)q.id)return 0;
        Vec3 pose=nrNodeAt(&q,s->timeUs);
        if(component(v->field,"position",&pose,x,-16000,16000)!=1)return 0;
        q.position=q.from=q.to=pose;q.atUs=s->timeUs;q.durationUs=0;matched=1;
    }
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;q.member=(int)x;matched=1;}
    INT("pinned",pinned,0,1) INT("minColumns",minColumns,8,NR_LAYOUT_MAX)
    INT("maxColumns",maxColumns,8,NR_LAYOUT_MAX) INT("padding",padding,0,8)
    INT("shaPrefix",shaPrefix,0,128) INT("showKind",showKind,0,1)
    INT("showStatus",showStatus,0,1) INT("showSha",showSha,0,1) INT("showDetail",showDetail,0,1)
    if(!strcmp(v->field,"color")){if(!(x>=0&&x<=0xffffff)||x!=(uint32_t)x)return 0;q.color=(uint32_t)x;matched=1;}
    if(!matched||q.minColumns>q.maxColumns||q.minColumns<=2*(q.padding+1))return 0;
    s->nodes[slot]=q;return 1;
#undef INT
}

int nrBindIndicatorValue(State*s,const Value*v,double x){
    for(int i=0;i<NR_INDICATORS;i++)if(s->indicators[i].used&&s->indicators[i].id==v->bindingId){
        Indicator q=s->indicators[i];int matched=0;
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;q.member=(int)x;matched=1;}
        INT("x",x,NR_LAYOUT_MIN,NR_LAYOUT_MAX) INT("y",y,NR_LAYOUT_MIN,NR_LAYOUT_MAX)
        INT("area",area,0,65535) INT("cursor",cursor,0,1)
        if(!strcmp(v->field,"material")){if(x<0||x>=NR_MATERIALS||x!=(int)x||!s->materials[(int)x].used)return 0;q.material=(int)x;matched=1;}
        if(!strcmp(v->field,"stepMs")){if(!duration(x,60000000,&q.stepUs)||!q.stepUs)return 0;matched=1;}
        if(!matched)return 0;s->indicators[i]=q;return 1;
#undef INT
    }return 0;
}

int nrBindSceneValue(State*s,const Value*v,double x){
    if(v->bindingFamily==23){
        if(v->bindingId||!(x==0||x==1))return 0;
        if(!strcmp(v->field,"reducedMotion")){s->reducedMotion=(int)x;return 1;}
        if(!strcmp(v->field,"screenReader")){s->screenReader=(int)x;return 1;}
        return 0;
    }
    if(v->bindingFamily==12){
        if(v->bindingId)return 0;Prompt*p=&s->promptDocument;int matched=0;
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;p->member=(int)x;matched=1;}
        INT("mode",mode,0,3) INT("border",border,0,4) INT("padding",padding,0,4) INT("active",active,0,1)
        INT("minRows",minRows,1,p->maxRows) INT("maxRows",maxRows,p->minRows,NR_LAYOUT_MAX)
        if(!strcmp(v->field,"alpha")){if(!(x>=0&&x<=1))return 0;p->alpha=x;matched=1;}
        if(matched)nrPointerRelease(s);return matched;
#undef INT
    }
    if(v->bindingFamily==13){
        if(v->bindingId)return 0;
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;s->member=(int)x;return 1;}
        INT("stars",stars,0,2000) INT("sampling",sampling,0,3) INT("style",style,0,5)
        if(!strcmp(v->field,"presentation")){if(s->schema<NR_STATE_SCHEMA_CANVAS_PRESENTATION||(x!=0&&x!=1))return 0;s->canvasPresentation=(uint32_t)x;return 1;}
        if(!strcmp(v->field,"background")){if(!(x>=0&&x<=0xffffff)||x!=(uint32_t)x)return 0;s->background=(uint32_t)x;return 1;}
        if(!strcmp(v->field,"starFar")){if(!(x>=20&&x<=1000))return 0;s->starFar=x;return 1;}
        if(!strcmp(v->field,"occlusionTint")){if(s->schema<NR_STATE_SCHEMA_OCCLUSION_CONTROLS||!(x>=0&&x<=1))return 0;s->occlusionControls.tintConfigured=1;s->occlusionControls.tint=x+0.0;return 1;}
        if(!strcmp(v->field,"occludedDots")){if(s->schema<NR_STATE_SCHEMA_OCCLUSION_CONTROLS||(x!=0&&x!=1))return 0;s->occlusionControls.occludedDots=(uint32_t)x;return 1;}
        return 0;
#undef INT
    }
    if(v->bindingFamily==14){
        for(int i=0;i<NR_FIELDS;i++)if(s->fields[i].used&&s->fields[i].id==(uint32_t)v->bindingId){
            Field q=s->fields[i];FieldControls controls=s->fieldControls[i];int matched=0;
#define NUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;q.member=x;matched=1;}
            NUM("x",x,NR_LAYOUT_MIN,NR_LAYOUT_MAX) NUM("y",y,NR_LAYOUT_MIN,NR_LAYOUT_MAX)
            NUM("width",width,.05,NR_LAYOUT_MAX) NUM("speed",speed,0,100) NUM("strength",strength,0,1)
            if(!strcmp(v->field,"lifeMs")){if(!duration(x,60000000,&q.lifeUs))return 0;matched=1;}
            if(!strcmp(v->field,"material")){if(x<0||x>=NR_MATERIALS||x!=(int)x||!s->materials[(int)x].used)return 0;q.material=(int)x;if(s->schema>=NR_STATE_SCHEMA_COLOR_FIELDS){nrFieldControlsInit(&controls);controls.materialAuthored=1;}matched=1;}
            const char*name=v->field;
            if(!strcmp(name,"rings")||!strcmp(name,"continuous")||!strcmp(name,"falloff")||!strcmp(name,"frequency")||!strcmp(name,"phase")||!strcmp(name,"interference")||!strncmp(name,"velocity.",9)||!strncmp(name,"surface.",8)){
                if(s->schema<NR_STATE_SCHEMA_COLOR_FIELDS)return 0;nrFieldControlsInit(&controls);
                if(!strcmp(name,"continuous")){if(x!=0&&x!=1)return 0;controls.continuous=(int)x;matched=1;}
                if(!strcmp(name,"rings")){if(s->schema<NR_STATE_SCHEMA_SOFT_FRONTS||!(x>=1&&x<=16)||x!=(int)x)return 0;if(NR_FIELD_OPTICS(&controls)>1)return 0;controls.rings=(controls.rings&~31u)|(uint32_t)x;matched=1;}
                if(!strcmp(name,"falloff")){if(!(x>=1&&x<=8)||x!=(int)x)return 0;controls.falloff=(int)x;matched=1;}
#define CONTROL(key,member,lo,hi) if(!strcmp(name,key)){if(!(x>=lo&&x<=hi))return 0;controls.member=x;matched=1;}
                CONTROL("frequency",frequency,0,1000) CONTROL("phase",phase,-3600,3600) CONTROL("interference",interference,0,1)
                CONTROL("velocity.x",vx,-100,100) CONTROL("velocity.y",vy,-100,100)
                if(!strncmp(name,"surface.",8)){if(!controls.surface)return 0;
                    CONTROL("surface.x",x,NR_LAYOUT_MIN,NR_LAYOUT_MAX) CONTROL("surface.y",y,NR_LAYOUT_MIN,NR_LAYOUT_MAX)
                    CONTROL("surface.width",width,.05,NR_LAYOUT_MAX) CONTROL("surface.height",height,.05,NR_LAYOUT_MAX)
                }
#undef CONTROL
            }
            if(matched){s->fields[i]=q;s->fieldControls[i]=controls;}return matched;
#undef NUM
        }
    }
    return 0;
}

int nrBindSurfaceValue(State*s,const Value*v,double x){
    if(!strncmp(v->field,"water.",6))return nrBindWaterValue(s,v,x);
    if(!strcmp(v->field,"thickness.width")||!strcmp(v->field,"thickness.speed"))return nrBindFlowThicknessValue(s,v,x);
    if(v->bindingId<1||v->bindingId>NR_SURFACES||!s->geometry.surfaces[v->bindingId-1].used)return 0;
    Surface q=s->geometry.surfaces[v->bindingId-1];int matched=0;
#define NUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;q.member=x;matched=1;}
#define INT(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi)||x!=(int)x)return 0;q.member=(int)x;matched=1;}
#define DUR(name,member,maximum) if(!strcmp(v->field,name)){if(!duration(x,maximum,&q.member))return 0;matched=1;}
    INT("collisionEnabled",collisionEnabled,0,1) INT("renderVisible",renderVisible,0,1)
    INT("maxIndividual",maxIndividual,0,NR_DEPOSITS) INT("maxTiles",maxTiles,0,NR_TILES) INT("overflow",overflow,0,1)
    NUM("restitution",restitution,0,1) NUM("friction",friction,0,1) NUM("settleSpeed",settleSpeed,0,30)
    NUM("reentrainWindSpeed",reentrain,0,256) NUM("wetnessGain",wetnessGain,0,10)
    NUM("evaporation",evaporation,0,10) NUM("heatGain",heatGain,0,10) NUM("cooling",cooling,0,10)
    NUM("thermalEvaporation",thermalEvaporation,0,10) NUM("wetnessDarkening",wetnessDarkening,0,1)
    NUM("heatTintStrength",heatTintStrength,0,1)
    DUR("retentionMs",retentionUs,86400000000ull) DUR("fadeMs",fadeUs,60000000ull)
    if(!strcmp(v->field,"heatColor")){if(!(x>=0&&x<=0xffffff)||x!=(uint32_t)x)return 0;q.heatColor=(uint32_t)x;matched=1;}
    if(!matched||(q.overflow&&!q.maxTiles)||(q.retentionUs&&q.fadeUs>q.retentionUs))return 0;
    s->geometry.surfaces[v->bindingId-1]=q;return 1;
#undef NUM
#undef INT
#undef DUR
}

int nrBindCellArtValue(State*s,const Value*v,double x){
    for(int i=0;i<4;i++)if(s->cellArt[i].used&&s->cellArt[i].id==v->bindingId){
        if(!strcmp(v->field,"alpha")){if(!(x>=0&&x<=1))return 0;s->cellArt[i].alpha=x;return 1;}
        if(!strcmp(v->field,"layer")){if(x!=0&&x!=1)return 0;s->cellArt[i].layer=(int)x;return 1;}
        if(!strcmp(v->field,"x")||!strcmp(v->field,"y")){
            if(!(x>=NR_LAYOUT_MIN&&x<=NR_LAYOUT_MAX)||x!=(int)x)return 0;
            if(v->field[0]=='x')s->cellArt[i].x=(int)x;else s->cellArt[i].y=(int)x;return 1;
        }return 0;
    }return 0;
}

/* Persisted authored binding shape is independent of current target existence.
 * A removed/indexed target stays dormant until an explicit write or rebinding. */
static int bindingFieldIn(const char*field,const char*names){
    size_t length=strlen(field);const char*p=names;
    while(*p){const char*start=p;while(*p&&*p!=' ')p++;if((size_t)(p-start)==length&&!memcmp(start,field,length))return 1;if(*p)p++;}
    return 0;
}
/* Schema-31 source authoring cannot carry fields introduced with schema 32.
 * Validate names without requiring a retained resource to still be live. */
int nrLegacyBindingShapeValid(const Value*v){
    if(!nrResourceBindingShapeValid(v)||v->bindingFamily>9)return 0;
    switch(v->bindingFamily){
    case 1:return bindingFieldIn(v->field,"alpha index hue lightness brightness channels.l channels.c channels.h channels.a channels.b channels.s channels.v channels.r channels.g channels.m channels.y channels.k channels.i");
    case 2:return bindingFieldIn(v->field,"alpha surfaceAlpha veinContrast windX windY windZ heat");
    case 3:return bindingFieldIn(v->field,"value alpha material backgroundMaterial selected enabled active x y width height padding min max mode pulseMs cellAspect innerRadius startAngle sweepAngle");
    case 5:return !bindingFieldIn(v->field,"border shape group text title");
    case 6:return !strcmp(v->field,"material");
    case 7:return !bindingFieldIn(v->field,"border layout parent");
    case 8:return !strcmp(v->field,"alpha");
    default:return 1;
    }
}
int nrResourceBindingShapeValid(const Value*v){
    int family=v->bindingFamily,id=v->bindingId;
    if(family==1){
        if(id<0||id>=NR_MATERIALS)return 0;
        if(bindingFieldIn(v->field,"hueStep spacing scope blend"))return 1;
        char base[32];memcpy(base,v->field,sizeof(base));const char*member="initial";
        char*dot=strrchr(base,'.');
        if(dot&&(strncmp(base,"channels.",9)||dot!=base+8)){member=v->field+(dot-base)+1;*dot=0;}
        return bindingFieldIn(base,"alpha index hue lightness brightness channels.l channels.c channels.h channels.a channels.b channels.s channels.v channels.r channels.g channels.m channels.y channels.k channels.i")&&
            bindingFieldIn(member,"initial rate min max step periodMs boundary easing seed");
    }
    if(family==2){
        if(nrBurstBindingField(v->field))return id>=1&&id<=65535;
        if(id<1||id>65535)return 0;
        const char*dot=strrchr(v->field,'.');
        if(dot){
            size_t n=(size_t)(dot-v->field);char base[32];memcpy(base,v->field,n);base[n]=0;
            return dot[1]&&(dot[1]=='x'||dot[1]=='y'||dot[1]=='z')&&!dot[2]&&
                bindingFieldIn(base,"position extent velocity spread gravity wind windVariation tumble shapeWeights birthOrientation initialOrientation angularVelocity");
        }
        return bindingFieldIn(v->field,"alpha surfaceAlpha veinContrast backTint twoSided heat drag lift flutterHz flutterAmount sizeMin sizeMax radius windScale windPeriodSeconds curl nearDistance farDistance farFadeDistance material sampling deposit collision topology count rate cycles gapMs runningTimeMs lifetimeMinMs lifetimeMaxMs tailMs trailMs birthFadeMs deathFadeMs coreMs windX windY windZ");
    }
    if(family==3&&!strncmp(v->field,"data.",5)){
        const char*p=v->field+5;int index=0;
        if(id<1||id>65535||*p<'0'||*p>'9'||(*p=='0'&&p[1]))return 0;
        while(*p>='0'&&*p<='9'){index=index*10+(*p++-'0');if(index>=128)return 0;}
        return !*p;
    }
    if(family==3)return id>=1&&id<=65535&&bindingFieldIn(v->field,"value alpha material backgroundMaterial selected enabled active x y width height padding min max mode pulseMs cellAspect innerRadius startAngle sweepAngle border sampling revealMs text data");
    if(family==4)return id>=0&&id<=65535&&bindingFieldIn(v->field,"position.x position.y position.z yaw pitch roll near far fov span orthographic");
    if(family==5)return id>=1&&id<=65535&&bindingFieldIn(v->field,"alpha material position.x position.y position.z yaw pitch roll width height minColumns maxColumns padding chromeSize fadeStartRatio fadeEndRatio anchorX anchorY overshoot scatter bend folds meshColumns meshRows durationMs border shape group text title");
    if(family==6)return id>=1&&id<=65535&&bindingFieldIn(v->field,"material x y width batchSize durationMs staggerMs jitterMs delayMs distance scatter variation wind overshoot cycles scrambleHz hueSpread reverseOrder randomOrder trailLength local phase easing text");
    if(family==7)return id>=1&&id<=65535&&bindingFieldIn(v->field,"alpha material x y width height padding margin speedX speedY hideEmpty fadeMs gapMs border layout parent");
    if(family==8)return id==0&&bindingFieldIn(v->field,"alpha enabled visible height restitution friction settleSpeed reentrainWindSpeed maxIndividual maxTiles overflow retentionMs fadeMs cellSize evaporation sampling");
    if(family==9)return id>=1&&id<=65535&&!strcmp(v->field,"active");
    if(family==10)return id>=1&&id<=65535&&bindingFieldIn(v->field,"position.x position.y position.z pinned color minColumns maxColumns padding shaPrefix showKind showStatus showSha showDetail label detail kind status sha");
    if(family==11)return id>=1&&id<=65535&&bindingFieldIn(v->field,"area x y stepMs material cursor sequence");
    if(family==12)return id==0&&bindingFieldIn(v->field,"mode alpha minRows maxRows border padding active");
    if(family==13)return id==0&&bindingFieldIn(v->field,"background stars starFar sampling style presentation occlusionTint occludedDots");
    if(family==14)return (uint32_t)id!=0&&bindingFieldIn(v->field,"x y width speed strength lifeMs material rings continuous falloff frequency phase interference velocity.x velocity.y surface.x surface.y surface.width surface.height");
    if(family<15)return 1;
    if(family==15)return id>=1&&id<=65535&&!strcmp(v->field,"flux");
    if(family==16)return id>=1&&id<=NR_SURFACES&&bindingFieldIn(v->field,"collisionEnabled renderVisible maxIndividual maxTiles overflow restitution friction settleSpeed reentrainWindSpeed retentionMs fadeMs wetnessGain evaporation heatGain cooling thermalEvaporation wetnessDarkening heatColor heatTintStrength thickness.width thickness.speed water.capacity water.evaporationUs");
    if(family==17){
        if(id<1||id>NR_SURFACES||strncmp(v->field,"waves.",6))return 0;
        const char*p=v->field+6;int index=0;
        if(*p<'0'||*p>'9'||(*p=='0'&&p[1]!='.'))return 0;
        while(*p>='0'&&*p<='9'){index=index*10+(*p++-'0');if(index>=32)return 0;}
        return *p=='.'&&bindingFieldIn(p+1,"amplitude kx kz omega phase");
    }
    if(family==18)return id>=1&&id<=65535&&bindingFieldIn(v->field,"mass radius fluidDensity gravity drag visible color surfaceId position.x position.y position.z velocity.x velocity.y velocity.z hull.angularVelocity.x hull.angularVelocity.y hull.angularVelocity.z hull.inertia.x hull.inertia.y hull.inertia.z");
    if(family==19)return id>=1&&id<=NR_SURFACES&&bindingFieldIn(v->field,"enabled sourceRate curvatureThreshold decay impactGain color velocity.x velocity.z");
    if(family==20)return id==0&&bindingFieldIn(v->field,"alpha color sampling");
    if(family==21)return id>=0&&id<NR_MESH&&bindingFieldIn(v->field,"alpha color thermal.power thermal.ambientTemperature thermal.conductance");
    if(family==22)return id>=1&&id<=65535&&bindingFieldIn(v->field,"x y alpha layer");
    if(family==24)return id>=1&&id<=65535&&bindingFieldIn(v->field,"speed jitter alpha flicker delayMs holdMs fadeMs repeatMs");
    if(family==23)return id==0&&bindingFieldIn(v->field,"reducedMotion screenReader");
    return 0;
}

/* Domains for dormant indexed resources. Live writes retain their normal
 * resource existence and coupled-state validation. */
int nrDormantBindingNumberValid(const Value*v,double x){
    if(!nrResourceBindingShapeValid(v)||!nrValueNumberValid(v,x))return 0;
    if(v->bindingFamily==24){
        if(!strcmp(v->field,"speed"))return x>=.001&&x<=10000;
        if(!strcmp(v->field,"jitter"))return x>=0&&x<=16;
        if(!strcmp(v->field,"alpha")||!strcmp(v->field,"flicker"))return x>=0&&x<=1;
        uint64_t us;return duration(x,86400000000ull,&us);
    }
    if(v->bindingFamily==16){
        if(!strncmp(v->field,"water.",6))return nrValueNumberValid(v,x);
        return (!strcmp(v->field,"thickness.width")||!strcmp(v->field,"thickness.speed"))&&x>=.000001&&x<=10000;
    }
    if(v->bindingFamily==17)return nrWaveBindingNumberValid(v,x);
    if(v->bindingFamily==18)return nrFloatBodyNumberValid(v,x);
    if(v->bindingFamily==21){
        if(!strncmp(v->field,"thermal.",8))return nrValueNumberValid(v,x);
        if(!strcmp(v->field,"alpha"))return x>=0&&x<=1;
        return !strcmp(v->field,"color")&&x>=0&&x<=0xffffff&&x==(uint32_t)x;
    }
    if(v->bindingFamily==22){
        if(!strcmp(v->field,"alpha"))return x>=0&&x<=1;
        if(!strcmp(v->field,"layer"))return x==0||x==1;
        return (!strcmp(v->field,"x")||!strcmp(v->field,"y"))&&x>=NR_LAYOUT_MIN&&x<=NR_LAYOUT_MAX&&x==(int)x;
    }
    return 0;
}
