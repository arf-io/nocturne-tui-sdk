#include "internal.h"
/* A fixed rational clock, with microsecond boundaries rounded down once.
 * This is the inverse of floor(step * 1e6 / 120), not a rounded increment. */
uint32_t nrStepAt(uint64_t us) { return (uint32_t)(((us+1)*120-1)/1000000); }
static int fail(NrContext *c,const char *message) {
    size_t n=strlen(message); if(n>255)n=255; memcpy(c->error,message,n);c->error[n]=0;return -1;
}
/* Scheduling and restore must probe the same promoted layout. */
static int promotePendingProbe(State*s){
    if(s->schema==NR_STATE_SCHEMA)return 1;
    nrFlowSprayPromote(s);
    if(s->schema<NR_STATE_SCHEMA_SURFACE_POSE)for(int i=0;i<NR_SURFACES;i++)if(s->angularFluids[i].used){
        s->surfacePoses[i].used=1;s->surfacePoses[i].orientation[3]=1;
    }
    if(s->schema<NR_STATE_SCHEMA_PROMPT_PRESENTATION)s->promptPresentation.ambiguous=1;
    /* Source queues from older writers retain their numeric policy while
     * probing the normalized full layout. Schema55 has the same payload as56.
     * Every schema from the phase-model epoch on probes under its own number:
     * normalising those down to 0x20261067 refused commands their writers
     * accepted (prompt-source needs 0x20261089), and newer features stay gated
     * by the snapshot's own epoch (a schema-97 queue still cannot carry a layer). */
    s->schema=s->schema>=NR_STATE_SCHEMA_TEXT_PHASE_MODEL?s->schema:s->schema>=NR_STATE_SCHEMA_TEXT_UINT32_SEED?NR_STATE_SCHEMA_TEXT_UINT32_SEED:s->schema>=NR_STATE_SCHEMA_TEXT_ALPHABET?NR_STATE_SCHEMA_TEXT_ALPHABET:s->schema>=NR_STATE_SCHEMA_STUDIO_NOVA?NR_STATE_SCHEMA_STUDIO_NOVA:s->schema>=NR_STATE_SCHEMA_WORLD_PROFILES?NR_STATE_SCHEMA_WORLD_PROFILES:s->schema>=NR_STATE_SCHEMA_THERMAL_PROFILES?NR_STATE_SCHEMA_THERMAL_PROFILES:s->schema>=NR_STATE_SCHEMA_ATELIER?NR_STATE_SCHEMA_ATELIER:s->schema>=NR_STATE_SCHEMA_KINETIC?NR_STATE_SCHEMA_KINETIC:s->schema>=NR_STATE_SCHEMA_OBSERVATORY?NR_STATE_SCHEMA_OBSERVATORY:s->schema>=NR_STATE_SCHEMA_CORONA?NR_STATE_SCHEMA_CORONA:s->schema>=NR_STATE_SCHEMA_WIDE_UNBOUND_VALUES?NR_STATE_SCHEMA_WIDE_UNBOUND_VALUES:NR_STATE_SCHEMA_RESOURCE_ANIMATION;s->foam.meshGeneration=s->geometry.meshGeneration;
    return nrSyncTextIdentities(s);
}
static int allowedChild(const Json*j) {
    int t=nrField(j,0,"op");
    return t>=0&&!nrEqual(j,t,"batch")&&!nrEqual(j,t,"schedule")&&
        !nrEqual(j,t,"cancel-schedule")&&!nrEqual(j,t,"time")&&!nrEqual(j,t,"reset")&&
        !nrEqual(j,t,"pointer")&&!nrEqual(j,t,"wheel")&&!nrEqual(j,t,"pause");
}
static int allowedScheduled(const Json*j){return allowedChild(j)||nrEqual(j,nrField(j,0,"op"),"batch");}
static int teardownShape(const Json*,int,int);
static int executePending(NrContext*c,State*s,const Json*j,int id){
    int previous=c->executingPendingId;c->executingPendingId=id;
    int result=nrTransaction(c,s,j);c->executingPendingId=previous;
    return result;
}
static int authorProbeTarget(NrContext*c,State*s,const char*op,int id){
    char command[64]="{\"op\":\"",digits[8];int used=(int)strlen(command),count=0;
    size_t length=strlen(op);memcpy(command+used,op,length);used+=(int)length;
    const char identity[]="\",\"id\":";memcpy(command+used,identity,sizeof(identity));used+=(int)sizeof(identity)-1;
    do{digits[count++]=(char)('0'+id%10);id/=10;}while(id);
    while(count)command[used++]=digits[--count];
    const char suffix[]="}";
    memcpy(command+used,suffix,sizeof(suffix));used+=(int)sizeof(suffix)-1;
    return nrParse(&c->repeatJson,command,used)?nrApply(c,s,&c->repeatJson):-1;
}
static int createProbeText(NrContext*c,State*s,int id,int*displaced){
    if(!c->checkingPending||s!=&c->probe)return -1;
    *displaced=-1;int available=0;
    for(int i=0;i<NR_TEXTS;i++)if(!s->text[i].used){available=1;break;}
    if(!available){*displaced=0;c->probeTextBackup=s->text[0];c->probeTextPhaseModelBackup=s->textPhaseModel[0];s->textPhaseModel[0]=0;memcpy(c->probeTextAlphabetTailBackup,s->textAlphabetTail[0],sizeof(c->probeTextAlphabetTailBackup));memset(&s->text[0],0,sizeof(TextRun));memset(s->textAlphabetTail[0],0,sizeof(s->textAlphabetTail[0]));}
    if(authorProbeTarget(c,s,"text",id)<0){
        if(*displaced>=0){s->text[*displaced]=c->probeTextBackup;s->textPhaseModel[*displaced]=c->probeTextPhaseModelBackup;memcpy(s->textAlphabetTail[*displaced],c->probeTextAlphabetTailBackup,sizeof(c->probeTextAlphabetTailBackup));}
        return -1;
    }
    for(int i=0;i<NR_TEXTS;i++)if(s->text[i].used&&s->text[i].id==id)return i;
    return -1;
}
static int createProbeNode(NrContext*c,State*s,int id,int*displaced){
    if(!c->checkingPending||s!=&c->probe)return -1;
    *displaced=-1;int available=0;
    for(int i=0;i<(int)NR_MAX_NODES;i++)if(!s->nodes[i].used){available=1;break;}
    if(!available){*displaced=0;c->probeNodeBackup=s->nodes[0];memset(&s->nodes[0],0,sizeof(Node));}
    if(authorProbeTarget(c,s,"node",id)<0){if(*displaced>=0)s->nodes[*displaced]=c->probeNodeBackup;return -1;}
    for(int i=0;i<(int)NR_MAX_NODES;i++)if(s->nodes[i].used&&s->nodes[i].id==id)return i;
    return -1;
}
static int createProbeEmitter(NrContext*c,State*s,int id,int*displaced){
    if(!c->checkingPending||s!=&c->probe)return -1;
    *displaced=-1;int available=0;
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(!s->emitters[i].used){available=1;break;}
    if(!available){
        *displaced=0;c->probeEmitterBackup=s->emitters[0];c->probeEmitterBirthBackup=s->birthOrientations[0];c->probeEmitterBurstBackup=s->burstControls[0];c->probeEmitterCoronaBackup=s->coronaControls[0];c->probeEmitterObservatoryBackup=s->observatoryControls[0];c->probeEmitterKineticBackup=s->kineticControls[0];c->probeEmitterKineticPaintBackup=s->kineticPaint[0];c->probeEmitterAtelierBackup=s->atelierControls[0];c->probeEmitterThermalSourceBackup=s->thermalSourceControls[0];c->probeEmitterWorldSourceBackup=s->worldSourceControls[0];c->probeEmitterStudioNovaBackup=s->studioNovaControls[0];
        memcpy(c->probeEmitterMotionBackup,&s->emitterMotions[0],sizeof(s->emitterMotions[0]));
        c->probeEmitterColliderBackup=s->geometry.emitterColliders[0];
        memcpy(c->probeEmitterSprayBackup,&s->flowSprays[0],sizeof(s->flowSprays[0]));
        memset(&s->flowSprays[0],0,sizeof(s->flowSprays[0]));memset(&s->emitters[0],0,sizeof(Emitter));
    }
    uint32_t generation=s->nextEmitterGeneration;
    if(generation==0xffffffffu)s->nextEmitterGeneration--;
    int result=authorProbeTarget(c,s,"emitter",id);s->nextEmitterGeneration=generation;
    if(result<0){
        if(*displaced>=0){
            s->emitters[0]=c->probeEmitterBackup;s->birthOrientations[0]=c->probeEmitterBirthBackup;s->burstControls[0]=c->probeEmitterBurstBackup;s->coronaControls[0]=c->probeEmitterCoronaBackup;s->observatoryControls[0]=c->probeEmitterObservatoryBackup;s->kineticControls[0]=c->probeEmitterKineticBackup;s->kineticPaint[0]=c->probeEmitterKineticPaintBackup;s->atelierControls[0]=c->probeEmitterAtelierBackup;s->thermalSourceControls[0]=c->probeEmitterThermalSourceBackup;s->worldSourceControls[0]=c->probeEmitterWorldSourceBackup;s->studioNovaControls[0]=c->probeEmitterStudioNovaBackup;
            memcpy(&s->emitterMotions[0],c->probeEmitterMotionBackup,sizeof(s->emitterMotions[0]));
            s->geometry.emitterColliders[0]=c->probeEmitterColliderBackup;
            memcpy(&s->flowSprays[0],c->probeEmitterSprayBackup,sizeof(s->flowSprays[0]));
        }
        return -1;
    }
    int slot=nrFindEmitter(s,id);if(slot<0)return -1;
    /* Host-authored counterparts are unknown until repair. Neutral extremes
     * preserve each scalar domain without constraining it to default lifetimes,
     * emission cycles, shape mixtures or distance/size intervals. */
    Emitter*q=&s->emitters[slot];q->sizeMin=.005;q->sizeMax=64;
    q->nearDistance=.001;q->farDistance=10000;q->farFade=0;
    q->shapeWeights=nrV(1,1,1);q->collision=1;q->deposit=0;
    q->count=100000;q->born=0;q->rate=0;q->cycles=1;q->gapUs=q->runningUs=q->startUs=0;
    q->lifeMinUs=1000;q->lifeMaxUs=3600000000ull;
    return slot;
}
static int probeResourceSet(NrContext*c,State*s,const Json*j){
    if(!c->checkingPending||s!=&c->probe||!nrEqual(j,nrField(j,0,"op"),"set")||
       !nrAllowed(j,0,"op path value expression intentId"))return -1;
    char path[128];if(nrString(j,nrField(j,0,"path"),path,sizeof(path))<0)return -1;
    int slot=-1;for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&!strcmp(s->values[i].path,path))slot=i;
    if(slot<0||s->values[slot].readonly||!nrResourceBindingShapeValid(&s->values[slot]))return -1;
    int value=nrField(j,0,"value"),expression=nrField(j,0,"expression"),intent=nrField(j,0,"intentId");
    if((expression>=0&&value>=0)||(expression<0&&intent>=0))return -1;
    Value*v=&s->values[slot];
    if(v->bindingFamily!=2&&!(v->bindingFamily==16&&(!strcmp(v->field,"thickness.width")||!strcmp(v->field,"thickness.speed")||!strncmp(v->field,"water.",6)))&&v->bindingFamily!=17&&v->bindingFamily!=18&&v->bindingFamily!=21&&v->bindingFamily!=22&&v->bindingFamily!=24)return -1;
    if(s->typedValues[slot].kind){
        int emitterFlag=v->bindingFamily==2&&(!strcmp(v->field,"twoSided")||!strcmp(v->field,"collision")||!strcmp(v->field,"deposit"));
        int bodyFlag=v->bindingFamily==18&&!strcmp(v->field,"visible");
        if(s->typedValues[slot].kind!=1||(!emitterFlag&&!bodyFlag))return -1;
        int family=v->bindingFamily;v->bindingFamily=0;
        int result=expression>=0?nrTypedExpression(c,s,slot,j,expression,intent):nrTypedSet(s,slot,j,value);
        v->bindingFamily=family;return result?0:-1;
    }
    double number=v->value;
    if(expression>=0){
        if(!nrNumericExpression(s,j,expression,intent,&number)&&!nrDataNumericExpression(c,s,j,expression,intent,&number))return -1;
    }else if(value>=0&&!nrNumber(j,value,&number))return -1;
    if(!(v->bindingFamily==2?nrEmitterNumberValid(c,s,v,number):nrDormantBindingNumberValid(v,number)))return -1;
    v->value=number;return 0;
}
static int applyTransactionChild(NrContext*c,State*s,const Json*j){
    GeometryIndex waveIndexBackup;int waveProbe=0;
    int widget=-1,kind=0,temporaryText=-1,displacedText=-1,temporaryNode=-1,displacedNode=-1,temporaryEmitter=-1,displacedEmitter=-1;
    /* A host can recreate missing resources or repair a changed widget kind.
     * Validate constant fields on compatible scratch resources, then discard
     * them before validating the resulting authored snapshot state. */
    if(c->checkingPending&&s==&c->probe&&nrEqual(j,nrField(j,0,"op"),"set")){
        char path[128];
        if(nrString(j,nrField(j,0,"path"),path,sizeof(path))>=0){
            for(int v=0;v<NR_VALUES;v++)if(s->values[v].used&&!strcmp(s->values[v].path,path)&&(s->values[v].bindingFamily==2||s->values[v].bindingFamily==3||s->values[v].bindingFamily==6||s->values[v].bindingFamily==10||s->values[v].bindingFamily==17)){
                if(s->values[v].bindingFamily==17){waveIndexBackup=s->geometry.index;waveProbe=1;break;}
                if(s->values[v].bindingFamily==2){
                    if(nrFindEmitter(s,s->values[v].bindingId)<0){
                        temporaryEmitter=createProbeEmitter(c,s,s->values[v].bindingId,&displacedEmitter);
                        if(temporaryEmitter<0)return -1;
                    }
                    break;
                }
                if(s->values[v].bindingFamily==10){
                    int found=0;for(int n=0;n<(int)NR_MAX_NODES;n++)if(s->nodes[n].used&&s->nodes[n].id==s->values[v].bindingId){found=1;break;}
                    if(!found){
                        temporaryNode=createProbeNode(c,s,s->values[v].bindingId,&displacedNode);
                        if(temporaryNode<0)return -1;
                        /* Missing authored counterparts are repairable host state.
                         * Keep each field's own domain strict without imposing
                         * the default node's unrelated min/max/padding relation. */
                        const char*field=s->values[v].field;Node*q=&s->nodes[temporaryNode];
                        if(!strcmp(field,"minColumns")){q->maxColumns=NR_LAYOUT_MAX;q->padding=0;}
                        else if(!strcmp(field,"maxColumns")){q->minColumns=8;q->padding=0;}
                        else if(!strcmp(field,"padding")){q->minColumns=22;q->maxColumns=NR_LAYOUT_MAX;}
                    }
                    break;
                }
                if(s->values[v].bindingFamily==6){
                    int found=0;for(int t=0;t<NR_TEXTS;t++)if(s->text[t].used&&s->text[t].id==s->values[v].bindingId){found=1;break;}
                    if(!found){temporaryText=createProbeText(c,s,s->values[v].bindingId,&displacedText);if(temporaryText<0)return -1;}
                    break;
                }
                const Value*value=&s->values[v];int plot=!strcmp(value->field,"sampling")||!strcmp(value->field,"revealMs");
                int circular=!strcmp(value->field,"cellAspect")||!strcmp(value->field,"startAngle")||!strcmp(value->field,"sweepAngle");
                int donut=!strcmp(value->field,"innerRadius");
                for(int w=0;w<NR_WIDGETS;w++)if(s->widgets[w].used&&s->widgets[w].id==value->bindingId){
                    int current=s->widgets[w].kind;
                    if((plot&&(current<6||current>13))||(circular&&current!=8&&current!=9)||(donut&&current!=9)){
                        widget=w;kind=current;s->widgets[w].kind=9;
                    }
                    break;
                }
                break;
            }
        }
    }
    int result=nrApply(c,s,j);
    if(result<0){
        if(waveProbe)s->geometry.index=waveIndexBackup;
        if(probeResourceSet(c,s,j)==0)result=0;
        if(c->checkingPending&&s==&c->probe&&nrFlowThicknessSettingsShape(j))result=0;
        if(c->checkingPending&&s==&c->probe&&nrThermalSettingsShape(j))result=0;
        if(c->checkingPending&&s==&c->probe&&nrFloatHullShape(j))result=0;
        if(c->checkingPending&&s==&c->probe&&nrSurfaceFluidShape(j))result=0;
        if(c->checkingPending&&s==&c->probe&&nrSurfaceFluidAngularShape(j))result=0;
        if(c->checkingPending&&s==&c->probe&&nrSurfaceWaterAddShape(j))result=0;
        if(c->checkingPending&&s==&c->probe&&nrSurfaceWaterSettingsShape(j))result=0;
    }
    if(widget>=0)s->widgets[widget].kind=kind;
    if(temporaryText>=0){
        if(displacedText>=0){s->text[displacedText]=c->probeTextBackup;s->textPhaseModel[displacedText]=c->probeTextPhaseModelBackup;memcpy(s->textAlphabetTail[displacedText],c->probeTextAlphabetTailBackup,sizeof(c->probeTextAlphabetTailBackup));}
        else{s->textPhaseModel[temporaryText]=0;memset(&s->text[temporaryText],0,sizeof(TextRun));memset(s->textAlphabetTail[temporaryText],0,sizeof(s->textAlphabetTail[temporaryText]));}
    }
    if(temporaryEmitter>=0){
        int slot=temporaryEmitter;
        if(displacedEmitter>=0){
            s->emitters[slot]=c->probeEmitterBackup;s->birthOrientations[slot]=c->probeEmitterBirthBackup;s->burstControls[slot]=c->probeEmitterBurstBackup;s->coronaControls[slot]=c->probeEmitterCoronaBackup;s->observatoryControls[slot]=c->probeEmitterObservatoryBackup;s->kineticControls[slot]=c->probeEmitterKineticBackup;s->kineticPaint[slot]=c->probeEmitterKineticPaintBackup;s->atelierControls[slot]=c->probeEmitterAtelierBackup;s->thermalSourceControls[slot]=c->probeEmitterThermalSourceBackup;s->worldSourceControls[slot]=c->probeEmitterWorldSourceBackup;s->studioNovaControls[slot]=c->probeEmitterStudioNovaBackup;
            memcpy(&s->emitterMotions[slot],c->probeEmitterMotionBackup,sizeof(s->emitterMotions[slot]));
            s->geometry.emitterColliders[slot]=c->probeEmitterColliderBackup;
            memcpy(&s->flowSprays[slot],c->probeEmitterSprayBackup,sizeof(s->flowSprays[slot]));
        }else{
            memset(&s->emitters[slot],0,sizeof(Emitter));s->birthOrientations[slot]=nrV(0,0,0);
            memset(&s->emitterMotions[slot],0,sizeof(s->emitterMotions[slot]));s->geometry.emitterColliders[slot]=0;
        }
    }
    if(temporaryNode>=0){
        if(displacedNode>=0)s->nodes[displacedNode]=c->probeNodeBackup;
        else memset(&s->nodes[temporaryNode],0,sizeof(Node));
    }
    return result;
}
static int probePending(NrContext*c,State*s,const Json*j,int id){
    int previous=c->checkingPending,deferred=c->deferValues,dirty=c->valuesDirty;
    char error[sizeof(c->error)];memcpy(error,c->error,sizeof(error));c->checkingPending=1;
    int result=executePending(c,s,j,id);c->checkingPending=previous;
    c->deferValues=deferred;c->valuesDirty=dirty;
    /* A successfully validated runtime fault is not the caller's last error. */
    if(result>=0)memcpy(c->error,error,sizeof(error));
    return result;
}
static int pendingBindingsValid(const State*source,const State*result){
    if(source->schema>=NR_STATE_SCHEMA_GENERAL_API)return 1;
    for(int i=0;i<NR_VALUES;i++)if(result->values[i].used&&!nrLegacyBindingShapeValid(&result->values[i]))return 0;
    return 1;
}
static void releaseEarlierPendingOwners(State*probe,uint64_t atUs,uint64_t sequence){
    for(int i=0;i<NR_PENDING;i++){
        PendingCommand*p=&probe->pending[i];
        if(p->used&&(p->atUs<atUs||(p->atUs==atUs&&p->sequence<sequence)))memset(p,0,sizeof(*p));
    }
}
static int uintField(const Json*j,const char*key,uint64_t*out,uint64_t max) {
    double v;int t=nrField(j,0,key);
    if(t<0||!nrNumber(j,t,&v)||v<0||v>max||v!=(uint64_t)v)return 0;
    *out=(uint64_t)v;return 1;
}
int nrTransaction(NrContext*c,State*s,const Json*j) {
    int op=nrField(j,0,"op");
    if(nrEqual(j,op,"batch")) {
        if(!nrAllowed(j,0,"op commands"))return fail(c,"Unknown batch parameter");
        int a=nrField(j,0,"commands");
        if(a<0||j->tokens[a].type!=J_ARRAY||j->tokens[a].count>64)return fail(c,"Batch requires at most 64 commands");
        int t=a+1,result=0;c->deferValues=1;c->valuesDirty=0;
        for(int i=0;i<j->tokens[a].count;i++) {
            if(j->tokens[t].type!=J_OBJECT){result=fail(c,"Batch entries must be objects");break;}
            if(!nrParse(&c->subjson,j->text+j->tokens[t].start,j->tokens[t].end-j->tokens[t].start)||!allowedChild(&c->subjson)){
                result=fail(c,"Batch cannot contain clock, routing, reset or nested transactions");break;
            }
            if(applyTransactionChild(c,s,&c->subjson)<0){
                /* A later consumer can block a previously registered removal.
                 * During import only, leave its live resource intact while
                 * validating the remaining ordinary children. Execution still
                 * rejects and rolls back the complete transaction. */
                if(c->checkingPending&&teardownShape(&c->subjson,0,0)==1){
                    if(nrEqual(&c->subjson,nrField(&c->subjson,0,"op"),"remove-value")){
                        char path[128];nrString(&c->subjson,nrField(&c->subjson,0,"path"),path,sizeof(path));
                        nrProbeReleaseValueConsumers(c,s,path);
                        if(applyTransactionChild(c,s,&c->subjson)<0){result=-1;break;}
                    }
                    t=j->tokens[t].next;continue;
                }
                result=-1;break;
            }
            t=j->tokens[t].next;
        }
        int dirty=c->valuesDirty;c->deferValues=0;c->valuesDirty=0;
        if(result>=0&&dirty&&!nrValuesTick(c,s))result=fail(c,"Batch trigger target rejected; transaction rolled back");
        return result;
    }
    if(nrEqual(j,op,"schedule")) {
        uint64_t id,at;int slot=-1;
        if(!nrAllowed(j,0,"op id atUs command")||!uintField(j,"id",&id,65535)||!id||!uintField(j,"atUs",&at,86400000000ull)||at<s->timeUs)return fail(c,"Invalid scheduled transaction identity/time");
        for(int i=0;i<NR_PENDING;i++) {
            if(s->pending[i].used&&s->pending[i].id==(int)id)return fail(c,"Scheduled transaction id already exists");
            if(!s->pending[i].used&&slot<0)slot=i;
        }
        if(slot<0)return fail(c,"Scheduled transaction capacity reached");
        int t=nrField(j,0,"command");
        if(t<0||j->tokens[t].type!=J_OBJECT)return fail(c,"Scheduled command object required");
        int n=j->tokens[t].end-j->tokens[t].start;
        if(n>=NR_PENDING_BYTES)return fail(c,"Scheduled command exceeds 4095 bytes");
        if(!nrParse(&c->scheduledJson,j->text+j->tokens[t].start,n)||!allowedScheduled(&c->scheduledJson))return fail(c,"Operation is not schedulable");
        nrStateCopy(&c->probe,s);c->counters.probeSyncs++;
        releaseEarlierPendingOwners(&c->probe,at,s->nextTransaction+1);
        /* Pending input executes after successful source-layout promotion. */
        if(!promotePendingProbe(&c->probe))return -1;
        if(nrTransaction(c,&c->probe,&c->scheduledJson)<0||!nrCountedValidState(c,&c->probe)||!nrValidateIntentPayloads(c,&c->probe)){
            if(!strcmp(c->error,"Prompt storage required")&&nrPromptMemorySize(c)>nrPromptMemoryCapacity(c))return -1;
            return fail(c,"Scheduled command fails validation against current state");
        }
        PendingCommand*p=&s->pending[slot];memset(p,0,sizeof(*p));
        p->used=1;p->id=(int)id;p->atUs=at;p->sequence=++s->nextTransaction;p->length=n;
        memcpy(p->command,j->text+j->tokens[t].start,(size_t)n);return 0;
    }
    if(nrEqual(j,op,"cancel-schedule")) {
        uint64_t id;
        if(!nrAllowed(j,0,"op id")||!uintField(j,"id",&id,65535))return fail(c,"Invalid cancellation");
        for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used&&s->pending[i].id==(int)id){memset(&s->pending[i],0,sizeof(PendingCommand));return 0;}
        return fail(c,"Scheduled transaction not found");
    }
    return applyTransactionChild(c,s,j);
}
int nrApplyScheduled(NrContext*c,State*s) {
    for(int count=0;count<NR_PENDING;count++) {
        int selected=-1;
        for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used&&s->pending[i].atUs<=s->timeUs) {
            if(selected<0||s->pending[i].atUs<s->pending[selected].atUs||
              (s->pending[i].atUs==s->pending[selected].atUs&&s->pending[i].sequence<s->pending[selected].sequence))selected=i;
        }
        if(selected<0)return 0;
        PendingCommand*p=&s->pending[selected];
        if(!nrParse(&c->scheduledJson,p->command,p->length)||!allowedScheduled(&c->scheduledJson)||executePending(c,s,&c->scheduledJson,p->id)<0)return -1;
        memset(p,0,sizeof(*p));
    }
    return 0;
}
/* Return one for a closed teardown-only command, zero for other operations,
 * and minus one for malformed teardown input. No resource is removed here. */
static int teardownShape(const Json*j,int at,int allowBatch){
    if(at<0||j->tokens[at].type!=J_OBJECT)return -1;
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"remove-value")){
        char path[128];
        return nrAllowed(j,at,"op path")&&nrString(j,nrField(j,at,"path"),path,sizeof(path))>=0&&path[0]=='/'?1:-1;
    }
    if(nrEqual(j,op,"remove-trigger")||nrEqual(j,op,"remove-style-rule")){
        double id;
        return nrAllowed(j,at,"op id")&&nrNumber(j,nrField(j,at,"id"),&id)&&id>=1&&id<=65535&&id==(int)id?1:-1;
    }
    if(allowBatch&&nrEqual(j,op,"batch")){
        int commands=nrField(j,at,"commands"),ordinary=0;
        if(!nrAllowed(j,at,"op commands")||commands<0||j->tokens[commands].type!=J_ARRAY||j->tokens[commands].count>64)return -1;
        for(int child=commands+1;child<j->tokens[commands].next;child=j->tokens[child].next){
            int valid=teardownShape(j,child,0);if(valid<0)return -1;if(!valid)ordinary=1;
        }
        return ordinary?0:1;
    }
    return 0;
}
/* Check only command/binding objects; arbitrary payload JSON is host data. */
static int pendingFoamFeature(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"surface-foam-transport"))return 1;
    int target=nrField(j,at,"target"),selector=nrField(j,at,"selector");
    if((nrEqual(j,nrField(j,at,"op"),"state-register")&&target>=0&&nrEqual(j,nrField(j,target,"family"),"electrical-arc"))||
       (nrEqual(j,nrField(j,at,"op"),"style-rule")&&selector>=0&&nrEqual(j,nrField(j,selector,"family"),"electrical-arc")))return 1;
    int binding=nrField(j,at,"binding");
    if(binding>=0&&nrEqual(j,nrField(j,binding,"family"),"surface-foam")&&
       (nrEqual(j,nrField(j,binding,"field"),"velocity.x")||nrEqual(j,nrField(j,binding,"field"),"velocity.z")))return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){
        int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)
            for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)
                if(pendingFoamFeature(j,child))return 1;
    }
    return 0;
}
static int pendingThicknessFeature(const Json*j,int at){
    int op=nrField(j,at,"op");if(nrEqual(j,op,"flow-thickness")||nrEqual(j,op,"flow-thickness-settings")||nrEqual(j,op,"remove-flow-thickness"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
        for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingThicknessFeature(j,child))return 1;}
    return 0;
}
static int pendingHullFeature(const Json*j,int at){
 int op=nrField(j,at,"op");if(nrEqual(j,op,"float-hull")||nrEqual(j,op,"remove-float-hull"))return 1;
 if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
  for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingHullFeature(j,child))return 1;}
 return 0;
}
static int pendingFluidFeature(const Json*j,int at){
 int op=nrField(j,at,"op");if(nrEqual(j,op,"surface-fluid")||nrEqual(j,op,"stop-surface-fluid"))return 1;
 if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
  for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingFluidFeature(j,child))return 1;}
 return 0;
}
static int pendingFluidExport(const Json*j,int at){
 if(nrEqual(j,nrField(j,at,"op"),"export-surface-fluid"))return 1;
 if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
  for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingFluidExport(j,child))return 1;}
 return 0;
}
static int pendingAngularFeature(const Json*j,int at){
 if(nrEqual(j,nrField(j,at,"op"),"surface-fluid-angular"))return 1;
 if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
  for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingAngularFeature(j,child))return 1;}
 return 0;
}
static int pendingPoseFeature(const Json*j,int at){
 if(nrEqual(j,nrField(j,at,"op"),"surface-fluid-angular")&&(nrField(j,at,"pivot")>=0||nrField(j,at,"orientation")>=0))return 1;
 if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
  for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingPoseFeature(j,child))return 1;}
 return 0;
}
/* An old angular layout can retain a live reservoir, but cannot schedule an
 * operation which needs the newer export ledger. Match the actual surface so
 * translation-only exports remain valid in their historical layouts. */
static void pendingAngularSurfaces(const Json*j,int at,unsigned char*surfaces){
 if(nrEqual(j,nrField(j,at,"op"),"surface-fluid-angular")){
  double id;if(nrNumber(j,nrField(j,at,"surfaceId"),&id)&&id>=1&&id<=NR_SURFACES&&id==(uint32_t)id)surfaces[(int)id-1]=1;
 }
 if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
  for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)pendingAngularSurfaces(j,child,surfaces);}
}
static int pendingAngularExport(const Json*j,int at,const unsigned char*surfaces){
 if(nrEqual(j,nrField(j,at,"op"),"export-surface-fluid")){
  double id;if(nrNumber(j,nrField(j,at,"surfaceId"),&id)&&id>=1&&id<=NR_SURFACES&&id==(uint32_t)id)
   return surfaces[(int)id-1]!=0;
 }
 if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
  for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingAngularExport(j,child,surfaces))return 1;}
 return 0;
}
static int pendingHydraulicHeatFeature(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"surface-water-link")&&nrField(j,at,"heatCapacityPerVolume")>=0)return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
        for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingHydraulicHeatFeature(j,child))return 1;}
    return 0;
}
static int pendingLatentHeatFeature(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"surface-water-thermal"))return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
        for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingLatentHeatFeature(j,child))return 1;}
    return 0;
}
static int pendingMeshSubdivisionFeature(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"mesh")&&nrField(j,at,"subdivisions")>=0)return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
        for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingMeshSubdivisionFeature(j,child))return 1;}
    return 0;
}
static int pendingBidiPrompt(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"prompt")&&(nrEqual(j,nrField(j,at,"layout"),"bidi")||nrField(j,at,"direction")>=0))return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int l=nrField(j,at,"commands");if(l>=0&&j->tokens[l].type==J_ARRAY)for(int c=l+1;c<j->tokens[l].next;c=j->tokens[c].next)if(pendingBidiPrompt(j,c))return 1;}return 0;
}
static int pendingPromptPresentation(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"prompt")&&(nrField(j,at,"layout")>=0||nrField(j,at,"ambiguousWidth")>=0))return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int l=nrField(j,at,"commands");if(l>=0&&j->tokens[l].type==J_ARRAY)for(int c=l+1;c<j->tokens[l].next;c=j->tokens[c].next)if(pendingPromptPresentation(j,c))return 1;}return 0;
}
static int pendingSourceOpticsFeature(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"field")&&nrField(j,at,"optics")>=0&&nrEqual(j,nrField(j,at,"optics"),"source"))return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int l=nrField(j,at,"commands");if(l>=0&&j->tokens[l].type==J_ARRAY)for(int c=l+1;c<j->tokens[l].next;c=j->tokens[c].next)if(pendingSourceOpticsFeature(j,c))return 1;}return 0;
}
static int pendingSoftFrontFeature(const Json*j,int at){
    int op=nrField(j,at,"op");if(nrEqual(j,op,"field")&&nrField(j,at,"rings")>=0)return 1;
    int b=nrField(j,at,"binding");if(b>=0&&nrEqual(j,nrField(j,b,"family"),"field")&&nrEqual(j,nrField(j,b,"field"),"rings"))return 1;
    if(nrEqual(j,op,"batch")){int l=nrField(j,at,"commands");if(l>=0&&j->tokens[l].type==J_ARRAY)for(int c=l+1;c<j->tokens[l].next;c=j->tokens[c].next)if(pendingSoftFrontFeature(j,c))return 1;}return 0;
}
static int pendingColorFieldFeature(const Json*j,int at){
    int op=nrField(j,at,"op");if(nrEqual(j,op,"remove-field"))return 1;
    int binding=nrField(j,at,"binding");if(binding>=0&&nrEqual(j,nrField(j,binding,"family"),"field")){
        const char*keys[]={"continuous","falloff","frequency","phase","interference","velocity.x","velocity.y","surface.x","surface.y","surface.width","surface.height"};
        for(int i=0;i<11;i++)if(nrEqual(j,nrField(j,binding,"field"),keys[i]))return 1;
    }
    if(nrEqual(j,op,"field")){const char*keys[]={"continuous","falloff","frequency","phase","interference","velocity","surface"};for(int i=0;i<7;i++)if(nrField(j,at,keys[i])>=0)return 1;}
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingColorFieldFeature(j,child))return 1;}
    return 0;
}
static int pendingAggregateReemitFeature(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"aggregate-reemit"))return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
        for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingAggregateReemitFeature(j,child))return 1;}
    return 0;
}
static int pendingMaterialHeatFeature(const Json*j,int at){
    int op=nrField(j,at,"op");if(nrEqual(j,op,"material-thermal")||nrEqual(j,op,"remove-material-thermal"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)
        for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingMaterialHeatFeature(j,child))return 1;}
    return 0;
}
static int pendingResourceAnimation(const Json*j,int at){
    int binding=nrField(j,at,"binding");
    if(binding>=0&&j->tokens[binding].type==J_OBJECT){
        if(nrEqual(j,nrField(j,binding,"family"),"electrical-arc"))return 1;
        if(nrEqual(j,nrField(j,binding,"family"),"emitter")){
            const char*fields[]={"glitterHz","glitterDepth","coreAlpha","residualMs","residualAlpha"};
            for(int i=0;i<5;i++)if(nrEqual(j,nrField(j,binding,"field"),fields[i]))return 1;
        }
    }
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)
            for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)
                if(pendingResourceAnimation(j,child))return 1;
    }return 0;
}
static int pendingWindowSourceGeometry(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"window")&&nrField(j,at,"sourceGeometry")>=0)return 1;
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingWindowSourceGeometry(j,child))return 1;}return 0;
}
static int pendingHighTextSeed(const Json*j,int at){
    if(nrEqual(j,nrField(j,at,"op"),"text")){int seed=nrField(j,at,"seed");double value;if(seed>=0&&nrNumber(j,seed,&value)&&value>2147483647.0)return 1;}
    if(nrEqual(j,nrField(j,at,"op"),"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingHighTextSeed(j,child))return 1;}return 0;
}
static int pendingExtendedTextAlphabet(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"text")){int alphabet=nrField(j,at,"alphabet");if(alphabet>=0){uint32_t glyphs[256];int n=nrDecode(j,alphabet,glyphs,256);if(n>128)return 1;}}
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingExtendedTextAlphabet(j,child))return 1;}return 0;
}
static int pendingStudioNovaStyle(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"studio-style")||nrEqual(j,op,"remove-studio-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingStudioNovaStyle(j,child))return 1;}
    return 0;
}
static int pendingWorldSourceStyle(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"world-style")||nrEqual(j,op,"remove-world-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingWorldSourceStyle(j,child))return 1;}
    return 0;
}
static int pendingThermalSourceStyle(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"thermal-style")||nrEqual(j,op,"remove-thermal-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingThermalSourceStyle(j,child))return 1;}
    return 0;
}
static int pendingAtelierStyle(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"atelier-style")||nrEqual(j,op,"remove-atelier-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingAtelierStyle(j,child))return 1;}
    return 0;
}
static int pendingKineticStyle(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"kinetic-style")||nrEqual(j,op,"remove-kinetic-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingKineticStyle(j,child))return 1;}
    return 0;
}
static int pendingObservatoryStyle(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"observatory-style")||nrEqual(j,op,"remove-observatory-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingObservatoryStyle(j,child))return 1;}
    return 0;
}
static int pendingCoronaStyle(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"corona-style")||nrEqual(j,op,"remove-corona-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingCoronaStyle(j,child))return 1;}
    return 0;
}
static int pendingBurstStyle(const Json*j,int at){
    int op=nrField(j,at,"op");if(nrEqual(j,op,"burst-style"))return 1;
    if(nrEqual(j,op,"batch")){int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)if(pendingBurstStyle(j,child))return 1;}
    return 0;
}
static int pendingElectricalArc(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"electrical-arc")||nrEqual(j,op,"remove-electrical-arc"))return 1;
    if(nrEqual(j,op,"batch")){
        int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)
            for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)
                if(pendingElectricalArc(j,child))return 1;
    }return 0;
}
/* Validate features under the source snapshot's schema before the execution
 * probe is promoted. Parsing a pending command with the current parser alone
 * would otherwise accept fields that its claimed source writer never knew. */
static int pendingWindowTexture(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"window-texture")||nrEqual(j,op,"remove-window-texture")||nrEqual(j,op,"window-content")||nrEqual(j,op,"remove-window-content"))return 1;
    if(nrEqual(j,op,"batch")){
        int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)
            for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)
                if(pendingWindowTexture(j,child))return 1;
    }
    return 0;
}
static int pendingRestorationFeature(const Json*j,int at){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"scene-art")||nrEqual(j,op,"remove-scene-art")||
       nrEqual(j,op,"source-stage-component")||nrEqual(j,op,"remove-source-stage-component"))return 1;
    if(nrEqual(j,op,"clear")&&nrEqual(j,nrField(j,at,"scope"),"scene-art"))return 1;
    if(nrEqual(j,op,"environment")&&nrField(j,at,"presentation")>=0)return 1;
    if(nrEqual(j,op,"define")||nrEqual(j,op,"bind")){
        int binding=nrField(j,at,"binding");
        if(binding>=0&&nrEqual(j,nrField(j,binding,"family"),"environment")&&
           nrEqual(j,nrField(j,binding,"field"),"presentation"))return 1;
    }
    if(nrEqual(j,op,"window")){
        static const char*fields[]={"sourcePresentation","depthFade","chrome","controlWidth",
            "controlHeight","customSide","customOrder","customGlyphs"};
        for(unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);i++)if(nrField(j,at,fields[i])>=0)return 1;
    }
    if(nrEqual(j,op,"text")&&nrField(j,at,"phaseModel")>=0)return 1;
    if(nrEqual(j,op,"material")&&nrField(j,at,"pattern")>=0)return 1;
    if(nrEqual(j,op,"prompt")){
        static const char*fields[]={"presentation","padding","paddingX","paddingY","margin",
            "inlineRows","inlineWidth","lineNumbers","selected","hueStep","hueSpeed",
            "huePeriodMs","maxChars","background","foreground","accent","selectionColor"};
        for(unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);i++)if(nrField(j,at,fields[i])>=0)return 1;
    }
    if(nrEqual(j,op,"batch")){
        int list=nrField(j,at,"commands");
        if(list>=0&&j->tokens[list].type==J_ARRAY)
            for(int child=list+1;child<j->tokens[list].next;child=j->tokens[child].next)
                if(pendingRestorationFeature(j,child))return 1;
    }
    return 0;
}
int nrCheckPending(NrContext*c,const State*s) {
    unsigned char angularSurfaces[NR_SURFACES]={0};
    if(s->schema<NR_STATE_SCHEMA_ANGULAR_HISTORY){
        for(int i=0;i<NR_SURFACES;i++)angularSurfaces[i]=s->angularFluids[i].used!=0;
        /* Collect across schedules before inspecting exports: a reservoir may
         * be created by a different queued command or inside a nested batch. */
        for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used){const PendingCommand*p=&s->pending[i];
            if(p->length<2||p->length>=NR_PENDING_BYTES||p->command[p->length]||!nrParse(&c->scheduledJson,p->command,p->length))return 0;
            pendingAngularSurfaces(&c->scheduledJson,0,angularSurfaces);
        }
    }
    for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used) {
        const PendingCommand*p=&s->pending[i];
        if(p->length<2||p->length>=NR_PENDING_BYTES||p->command[p->length]||!nrParse(&c->scheduledJson,p->command,p->length)||!allowedScheduled(&c->scheduledJson))return 0;
        if(s->schema<NR_STATE_SCHEMA_WINDOW_TEXTURE&&pendingWindowTexture(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_TEXT_PHASE_MODEL&&pendingRestorationFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_RESOURCE_ANIMATION&&pendingResourceAnimation(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_WINDOW_SOURCE&&pendingWindowSourceGeometry(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_TEXT_UINT32_SEED&&pendingHighTextSeed(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_TEXT_ALPHABET&&pendingExtendedTextAlphabet(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_STUDIO_NOVA&&pendingStudioNovaStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_WORLD_PROFILES&&pendingWorldSourceStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_THERMAL_PROFILES&&pendingThermalSourceStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_ATELIER&&pendingAtelierStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_KINETIC&&pendingKineticStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_OBSERVATORY&&pendingObservatoryStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_CORONA&&pendingCoronaStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_BURST_CONTROLS&&pendingBurstStyle(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_ELECTRICAL_ARCS&&pendingElectricalArc(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_BIDI_PROMPT&&pendingBidiPrompt(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_PROMPT_PRESENTATION&&pendingPromptPresentation(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_SOURCE_OPTICS&&pendingSourceOpticsFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_SOFT_FRONTS&&pendingSoftFrontFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_COLOR_FIELDS&&pendingColorFieldFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_MESH_SUBDIVISION&&pendingMeshSubdivisionFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_AGGREGATE_REEMIT&&pendingAggregateReemitFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_MATERIAL_HEAT&&pendingMaterialHeatFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_LATENT_HEAT&&pendingLatentHeatFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_HYDRAULIC_HEAT&&pendingHydraulicHeatFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_FLOW_THICKNESS&&pendingThicknessFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_FLOAT_HULLS&&pendingHullFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_SURFACE_FLUID&&pendingFluidFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_FLUID_HISTORY&&pendingFluidExport(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_ANGULAR_FLUID&&pendingAngularFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_SURFACE_POSE&&pendingPoseFeature(&c->scheduledJson,0))return 0;
        if(s->schema<NR_STATE_SCHEMA_ANGULAR_HISTORY&&pendingAngularExport(&c->scheduledJson,0,angularSurfaces))return 0;
        if(s->schema<NR_STATE_SCHEMA_FOAM_TRANSPORT&&pendingFoamFeature(&c->scheduledJson,0))return 0;
        /* Later consumers or removals can block a previously accepted teardown.
         * Persist that recoverable state without accepting malformed commands. */
        int teardown=teardownShape(&c->scheduledJson,0,1);
        if(teardown<0)return 0;if(teardown)continue;
        /* Validate without advancing state, firing actions, or borrowing a host. */
        nrStateCopy(&c->probe,s);c->counters.probeSyncs++;
        releaseEarlierPendingOwners(&c->probe,p->atUs,p->sequence);
        /* Pending input executes after successful source-layout promotion. */
        if(!promotePendingProbe(&c->probe))return 0;
        if(probePending(c,&c->probe,&c->scheduledJson,p->id)<0||!nrCountedValidState(c,&c->probe)||!nrValidateIntentPayloads(c,&c->probe)||!pendingBindingsValid(s,&c->probe))return 0;
    }
    return 1;
}
