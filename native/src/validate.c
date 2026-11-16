#include "internal.h"
/* Restore treats even a valid-CRC snapshot as untrusted. Length/count checks
 * precede every traversal; all potentially consumed strings are terminated. */
static int bounded(double v,double lo,double hi) {
    return v>=lo&&v<=hi;
}
static int flag(int v) {
    return v==0||v==1;
}
static int vector(Vec3 v,double b) {
    return bounded(v.x,-b,b)&&bounded(v.y,-b,b)&&bounded(v.z,-b,b);
}
static int string(const char*s,size_t n) {
    for(size_t i=0; i<n; i++)if(!s[i])return 1;
    return 0;
}
static int glyphs(const uint32_t*p,int n,int cap) {
    if(n<0||n>cap)return 0;
    for(int i=0; i<n; i++) {
        uint32_t g=p[i];
        if(g>0x10ffffu||(g>=0xd800&&g<=0xdfff)||(g<32&&g!=9&&g!=10&&g!=11&&g!=12&&g!=13))return 0;
    }
    return 1;
}
int nrValidGlyphs(const uint32_t*p,int n,int cap){return glyphs(p,n,cap);}
static int track(const Track*t) {
    return bounded(t->initial,-10000,10000)&&bounded(t->min,-10000,10000)&&bounded(t->max,t->min,10000)&&bounded(t->rate,-10000,10000)&&bounded(t->step,-10000,10000)&&t->periodUs>0&&t->periodUs<=3600000000ull&&t->boundary>=0&&t->boundary<=4&&t->easing>=0&&t->easing<=6;
}
static int camera(const Camera*c,uint32_t schema) {
    return vector(c->position,100000)&&bounded(c->yaw,-36000,36000)&&bounded(c->pitch,schema>=NR_STATE_SCHEMA_CAMERA_CONTROLS?-90:-89.9,schema>=NR_STATE_SCHEMA_CAMERA_CONTROLS?90:89.9)&&bounded(c->roll,-36000,36000)&&bounded(c->nearPlane,.001,100)&&bounded(c->farPlane,c->nearPlane+.0001,1000000)&&bounded(c->fov,10,150)&&bounded(c->span,.1,2000)&&flag(c->orthographic);
}
static int materialRef(int id) {
    return id>=0&&id<NR_MATERIALS;
}
static int particleMotionValid(Vec3 orientation,Vec3 angular,int authored,int padding) {
    if(!flag(authored)||padding||!vector(orientation,3600)||!vector(angular,720))return 0;
    return authored||!(orientation.x||orientation.y||orientation.z||angular.x||angular.y||angular.z);
}
/* Unconfigured controls are canonical zeros (tint default 1); configured tint lies in 0..1. */
static int occlusionControlsValid(const OcclusionControls*q) {
    if(q->tintConfigured>1u||q->occludedDots>1u)return 0;
    uint64_t bits;memcpy(&bits,&q->tint,sizeof(bits));
    return q->tintConfigured?bounded(q->tint,0,1):bits==0;
}
/* nrValidState's widget clauses: one record and the clock, nothing else (the direct widget commit's validator). */
int nrValidWidget(const State*s,const Widget*w){
    if(!flag(w->used))return 0;
    if(w->used&&(w->id<1||w->id>65535||w->kind<0||w->kind>17||w->width<1||w->height<1||w->padding<0||w->padding>8||w->border<0||w->border>4||!materialRef(w->material)||(w->backgroundMaterial< -1||w->backgroundMaterial>=NR_MATERIALS)||!flag(w->enabled)||!flag(w->selected)||!flag(w->active)||!glyphs(w->text,w->count,NR_MAX_TEXT)||w->dataCount<0||w->dataCount>128||w->mode<0||w->mode>15||!bounded(w->value,-1000000,1000000)||!bounded(w->min,-1000000,1000000)||!bounded(w->max,w->min,1000000)||w->max==w->min||!bounded(w->alpha,0,1)||w->changedUs>s->timeUs||w->pulseUs>60000000))return 0;
    if(w->used&&(w->sampling< -1||w->sampling>3||!bounded(w->cellAspect,.5,4)||!bounded(w->innerRadius,0,.98)||!bounded(w->startAngle,-36000,36000)||!bounded(w->sweepAngle,0,360)||w->revealUs>60000000||w->revealAtUs>s->timeUs))return 0;
    if(w->dataCount<0||w->dataCount>128)return 0;
    for(int k=0; k<w->dataCount; k++)if(!bounded(w->data[k],-1000000,1000000))return 0;
    return 1;
}
/* nrValidState's camera and flight clauses (extracted unchanged). */
static int cameraFlightValid(const State*s){
    if(!camera(&s->camera,s->schema)||s->flight.count<0||s->flight.count>NR_STEPS||s->flight.startUs>s->timeUs||!vector(s->flight.look,36000))return 0;
    if(s->flight.count&&!camera(&s->flight.origin,s->schema))return 0;
    for(int i=0; i<s->flight.count; i++) {
        const Motion*m=&s->flight.steps[i];
        if(m->kind<0||m->kind>7||!flag(m->coordinated)||!m->durationUs||m->durationUs>3600000000ull||!bounded(m->speed,-100,100)||!bounded(m->yaw,-3600,3600)||!bounded(m->pitch,-89,89)||!bounded(m->roll,-3600,3600)||!bounded(m->bank,-85,85)||!bounded(m->radius,1,2000)||!vector(m->target,10000))return 0;
    }
    return 1;
}
/* Every validator that reads what a direct pointer, wheel or camera-input gesture writes (TRANSACTIONS.md,
 * "pointer"): the camera and flight clauses, the pointer clauses, the prompt caret and anchor bounds, the original
 * camera and the camera controls. */
int nrValidPointerCamera(const State*s){
    const Prompt*p=&s->promptDocument;
    return cameraFlightValid(s)&&flag(s->pointerActive)&&s->pointerKind>=0&&s->pointerKind<=3&&bounded(s->pointerX,-2147483647.0/2,2147483647.0/2)&&
        bounded(s->pointerY,-2147483647.0/4,2147483647.0/4)&&p->caret>=0&&p->caret<=p->count&&p->anchor>=-1&&p->anchor<=p->count&&
        nrValidOriginalCamera(s)&&nrValidCameraControls(s);
}
/* nrValidState's node clauses: one record and the clock (the direct node commit's validator). */
int nrValidNode(const State*s,const Node*n){
    if(!flag(n->used))return 0;
    if(n->used&&(n->minColumns<8||n->maxColumns<n->minColumns||n->padding<0||n->padding>8||n->minColumns<=2*(n->padding+1)||n->shaPrefix<0||n->shaPrefix>128||!flag(n->showKind)||!flag(n->showStatus)||!flag(n->showSha)||!flag(n->showDetail)))return 0;
    if(n->used&&(n->id<1||n->id>65535||!flag(n->pinned)||!glyphs(n->label,n->labelCount,256)||!glyphs(n->detail,n->detailCount,512)||!string(n->kind,sizeof(n->kind))||!string(n->status,sizeof(n->status))||!string(n->sha,sizeof(n->sha))||!vector(n->position,16000)||!vector(n->from,16000)||!vector(n->to,16000)||n->color>0xffffffu||n->atUs>s->timeUs||n->durationUs>60000000))return 0;
    return 1;
}
int nrValidState(const State*s) {
    if(!nrValidPromptAppearance(s)||!nrValidCameraControls(s)||!nrValidFirstPrompt(s)||!nrValidOriginalCamera(s)||!nrValidSourceGraphLayout(s)||!nrValidSourceSky(s))return 0;
    if(!nrPromptFramedValid(s)||!nrPromptStorageValid(s)||!nrValidWindowApplication(s)||!nrValidAtelierWindows(s)||!nrValidAtelierApplicationParticles(s))return 0;
    if(!nrValidMaterialPatterns(s)||!nrValidWindowTextures(s)||!nrValidWindowContent(s))return 0;
    if(!nrValidSceneArt(s)||!nrValidWindowPresentation(s)||!nrValidSourceStage(s)||!nrValidSourceStageScene(s)||!nrValidSourceModal(s)||!nrValidSourceModel(s)||!nrValidOriginalObservatoryOverlay(s))return 0;
    if(s->canvasPresentation>1||s->canvasReserved||(s->schema<NR_STATE_SCHEMA_CANVAS_PRESENTATION&&s->canvasPresentation))return 0;
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(!s->windowPresentation[i].enabled&&!s->atelierWindows[i].enabled&&s->windowSourceOrder[i])return 0;
    const RepeatEdit*r=&s->repeatEdit;
    if(!flag(r->unit)||!flag(r->append)||r->selected < -1||r->selected>26||(r->append&&r->selected<=0)||r->count<0||r->count>9999)return 0;
    if(r->key){
        if(!r->count||(r->key!='d'&&r->key!='x'&&r->key!='X'&&r->key!='D'))return 0;
        if(r->key=='d'){int valid=0;const char*motions="dwbeWBEhjkl0^$";for(int k=0;motions[k];k++)if(r->motion==motions[k])valid=1;if(!valid)return 0;}
        else if(r->motion)return 0;
    }else if(r->motion||r->count||r->unit||r->selected||r->append)return 0;
    if(s->editorRedo.count<0||s->editorRedo.count>NR_PROMPT_HISTORY||s->promptDocument.undoSize<0||s->promptDocument.undoSize>NR_PROMPT_HISTORY||s->editorRedo.count+s->promptDocument.undoSize>NR_PROMPT_HISTORY||s->editorRedo.padding)return 0;
    if(!flag(s->promptRegisters.pending)||!flag(s->promptRegisters.append)||s->promptRegisters.selected < -1||s->promptRegisters.selected>26||s->promptRegisters.padding||s->promptRegisters.revision>s->promptDocument.revision||(s->promptRegisters.append&&s->promptRegisters.selected<=0)||(s->promptRegisters.pending&&(s->promptRegisters.selected||s->promptRegisters.append)))return 0;
    for(int i=0;i<26;i++)if(!glyphs(s->promptRegisters.slots[i].glyphs,s->promptRegisters.slots[i].count,s->dynamicPrompt.capacity)||!flag(s->promptRegisters.slots[i].linewise))return 0;
    if(!glyphs(s->promptRegister.glyphs,s->promptRegister.count,s->dynamicPrompt.capacity)||!flag(s->promptRegister.linewise))return 0;
    if((s->vimOperator.key!=0&&s->vimOperator.key!='d'&&s->vimOperator.key!='c'&&!((s->schema>=NR_STATE_SCHEMA_GENERAL_API||s->schema==NR_STATE_SCHEMA_CELL_ART||s->schema==NR_STATE_SCHEMA_THERMAL_LINK||s->schema==NR_STATE_SCHEMA_THERMAL_TRANSFER||s->schema==NR_STATE_SCHEMA_THERMAL||s->schema==NR_STATE_SCHEMA_WATER_REEMIT||s->schema==NR_STATE_SCHEMA_WATER_LINK||s->schema==NR_STATE_SCHEMA_WATER_TRANSFER||s->schema==NR_STATE_SCHEMA_SURFACE_WATER||s->schema==NR_STATE_SCHEMA_SPRAY_PARTICLES||s->schema==NR_STATE_SCHEMA_FLOW_SPRAY||s->schema==NR_STATE_SCHEMA_FLOW_SINK||s->schema==NR_STATE_SCHEMA_FLOW_SURFACE||s->schema==NR_STATE_SCHEMA_FLOW||s->schema==NR_STATE_SCHEMA_REPEAT_EDIT||s->schema==NR_STATE_SCHEMA_EDITOR_REDO||s->schema==NR_STATE_SCHEMA_NAMED_REGISTERS||s->schema==NR_STATE_SCHEMA_VIM_REGISTER)&&s->vimOperator.key=='y'))||s->vimOperator.count<0||s->vimOperator.count>9999||(s->vimOperator.key&&!s->vimOperator.count)||s->vimOperator.revision>s->promptDocument.revision)return 0;
    if(s->vimCount.count<0||s->vimCount.count>9999||s->vimCount.padding||s->vimCount.revision>s->promptDocument.revision)return 0;
    for(int i=0;i<4;i++){
        if(!flag(s->cellArt[i].used))return 0;if(!s->cellArt[i].used)continue;
        if(s->cellArt[i].id<1||s->cellArt[i].id>65535||s->cellArt[i].width<1||s->cellArt[i].width>2048||s->cellArt[i].height<1||s->cellArt[i].height>2048||
           s->cellArt[i].width*s->cellArt[i].height>2048||
           !flag(s->cellArt[i].layer)||s->cellArt[i].padding||!bounded(s->cellArt[i].alpha,0,1))return 0;
        for(int j=0;j<i;j++)if(s->cellArt[j].used&&s->cellArt[j].id==s->cellArt[i].id)return 0;
        for(int k=0;k<s->cellArt[i].width*s->cellArt[i].height;k++){
            uint32_t g=s->cellArt[i].cells[k][0];if((g&&g<32)||g>0x10ffffu||(g>=0xd800&&g<=0xdfff)||s->cellArt[i].cells[k][1]>0xffffff||s->cellArt[i].cells[k][2]>0xffffff)return 0;
        }
    }
    if(s->schema<NR_STATE_SCHEMA_PROMPT_PRESENTATION){if(s->promptPresentation.layout||s->promptPresentation.ambiguous)return 0;}else if(s->promptPresentation.layout<0||(s->promptPresentation.layout>1&&(s->schema<NR_STATE_SCHEMA_BIDI_PROMPT||(s->promptPresentation.layout!=2&&s->promptPresentation.layout!=6&&s->promptPresentation.layout!=10)))||s->promptPresentation.ambiguous<1||s->promptPresentation.ambiguous>2)return 0;
    if(!nrValidStudioNovaControls(s)||!nrValidWorldSourceControls(s)||!nrValidThermalSourceControls(s)||!nrValidAtelierControls(s)||!nrValidKineticControls(s)||!nrValidObservatoryControls(s)||!nrValidCoronaControls(s)||!nrValidNovaOptics(s)||!nrValidBurstControls(s)||!nrValidElectricalArcs(s)||!nrValidFieldControls(s)||!nrValidTextIdentities(s)||!nrValidFlowThickness(s)||!nrValidSurfaceWaves(s)||!nrValidFloatBodies(s)||!nrValidFloatHulls(s)||!nrValidSurfaceFluids(s)||!nrValidFoam(s)||!nrValidPathActors(s)||!nrValidFlows(s)||!nrValidFlowSinks(s)||!nrValidFlowSprays(s)||!nrValidSprayParticles(s)||!nrValidSurfaceWater(s)||!nrValidWaterLinks(s)||!nrValidThermal(s)||!nrValidThermalLinks(s)||!nrValidMaterialHeat(s)||!nrValidAggregateProvenance(s))return 0;
    if(s->schema>NR_STATE_SCHEMA||s->magic!=NR_MAGIC||(s->schema<NR_STATE_SCHEMA_GENERAL_API&&s->schema!=NR_STATE_SCHEMA_CELL_ART&&s->schema!=NR_STATE_SCHEMA_THERMAL_LINK&&s->schema!=NR_STATE_SCHEMA_THERMAL_TRANSFER&&s->schema!=NR_STATE_SCHEMA_THERMAL&&s->schema!=NR_STATE_SCHEMA_WATER_REEMIT&&s->schema!=NR_STATE_SCHEMA_WATER_LINK&&s->schema!=NR_STATE_SCHEMA_WATER_TRANSFER&&s->schema!=NR_STATE_SCHEMA_SURFACE_WATER&&s->schema!=NR_STATE_SCHEMA_SPRAY_PARTICLES&&s->schema!=NR_STATE_SCHEMA_FLOW_SPRAY&&s->schema!=NR_STATE_SCHEMA_FLOW_SINK&&s->schema!=NR_STATE_SCHEMA_FLOW_SURFACE&&s->schema!=NR_STATE_SCHEMA_FLOW&&s->schema!=NR_STATE_SCHEMA_REPEAT_EDIT&&s->schema!=NR_STATE_SCHEMA_EDITOR_REDO&&s->schema!=NR_STATE_SCHEMA_NAMED_REGISTERS&&s->schema!=NR_STATE_SCHEMA_VIM_REGISTER&&s->schema!=NR_STATE_SCHEMA_VIM_OPERATOR&&s->schema!=NR_STATE_SCHEMA_VIM_COUNT&&s->schema!=NR_STATE_SCHEMA_PATH_ACTORS&&s->schema!=NR_STATE_SCHEMA_FOAM&&s->schema!=NR_STATE_SCHEMA_FLOAT_BODIES&&s->schema!=NR_STATE_SCHEMA_SURFACE_WAVES&&s->schema!=NR_STATE_SCHEMA_PARTICLE_MOTION&&s->schema!=NR_STATE_SCHEMA_BIRTH_FRAME&&s->schema!=NR_STATE_SCHEMA_GEOMETRY&&s->schema!=NR_STATE_SCHEMA_PRE_GEOMETRY&&s->schema!=NR_STATE_SCHEMA_LOCAL_ACTION&&s->schema!=NR_STATE_SCHEMA_LOCAL_SELECTOR&&s->schema!=NR_STATE_SCHEMA_CONTRACTS7&&s->schema!=NR_STATE_SCHEMA_OLDEST)||!nrValidViewport(s->width,s->height)||s->paused>1||s->timeUs>86400000000ull||s->targetUs>86400000000ull||s->targetUs<s->timeUs||s->step>10368000||!s->nextParticle||!s->nextField)return 0;
    if(!cameraFlightValid(s))return 0;
    const Prompt*p=&s->promptDocument;
    if(!glyphs(p->glyphs,p->count,s->dynamicPrompt.capacity)||p->caret<0||p->caret>p->count||p->anchor < -1||p->anchor>p->count||p->mode<0||p->mode>3||!flag(p->active)||!flag(p->modal)||!flag(p->vimMode)||p->minRows<1||p->maxRows<p->minRows||p->undoSize<0||p->undoSize>NR_PROMPT_HISTORY||p->undoHead<0||p->undoHead>=NR_PROMPT_HISTORY||p->padding<0||p->padding>4||p->border<0||p->border>4||!bounded(p->alpha,0,1))return 0;
    for(int i=0; i<NR_PROMPT_HISTORY; i++)if(!glyphs(p->undo[i],p->undoCount[i],s->dynamicPrompt.capacity)||p->undoCaret[i]<0||p->undoCaret[i]>p->undoCount[i])return 0;
    if(!flag(s->reducedMotion)||!flag(s->screenReader)||s->dockPage<0||s->dockPage>(int)NR_MAX_WINDOWS)return 0;
    for(int i=0;i<NR_PENDING;i++) {
        const PendingCommand*q=&s->pending[i];if(!flag(q->used))return 0;
        if(q->used&&(q->id<1||q->id>65535||q->length<2||q->length>=NR_PENDING_BYTES||q->command[q->length]||q->atUs>86400000000ull||!q->sequence||q->sequence>s->nextTransaction))return 0;
        for(int j=0;j<i;j++)if(q->used&&s->pending[j].used&&(q->id==s->pending[j].id||q->sequence==s->pending[j].sequence))return 0;
    }
    if(s->step!=nrStepAt(s->timeUs))return 0;
    const Floor*f=&s->floor;
    if(f->sampling<0||f->sampling>3||s->meshSampling<0||s->meshSampling>3)return 0;
    if(f->fadeUs>60000000||!bounded(f->wetness,0,1)||!bounded(f->evaporation,0,10))return 0;
    if(!flag(f->enabled)||!flag(f->visible)||f->maxIndividual<0||f->maxIndividual>NR_DEPOSITS||f->maxTiles<0||f->maxTiles>NR_TILES||!flag(f->overflow)||!bounded(f->height,-1000,1000)||!bounded(f->restitution,0,1)||!bounded(f->friction,0,1)||!bounded(f->settleSpeed,0,30)||!bounded(f->reentrain,0,256)||!bounded(f->cellSize,.1,100)||!bounded(f->alpha,0,1)||f->retentionUs>86400000000ull)return 0;
    for(int i=0; i<(int)NR_MAX_EMITTERS; i++) {
        const Emitter*e=&s->emitters[i];
        if(!particleMotionValid(s->emitterMotions[i].orientation,s->emitterMotions[i].angularVelocity,s->emitterMotions[i].authored,s->emitterMotions[i].padding))return 0;
        if(e->used&&s->emitterMotions[i].authored&&nrEffectAlgorithm(e->effect)!=0&&nrEffectAlgorithm(e->effect)!=2)return 0;
        if(!e->used&&s->emitterMotions[i].authored)return 0;
        if(!vector(s->birthOrientations[i],3600))return 0;
        if(!e->used&&(s->birthOrientations[i].x||s->birthOrientations[i].y||s->birthOrientations[i].z))return 0;
        if(e->used&&(e->sampling<0||e->sampling>3||!bounded(e->surfaceAlpha,0,1)))return 0;
        if(e->used&&(!e->generation||e->generation>s->nextEmitterGeneration))return 0;
        if(!flag(e->used))return 0;
        if(!e->used)continue;
        if(!nrEndStyleSupported(e->effect,e->endStyle))return 0;
        if(e->cycles<1||e->cycles>10000||e->gapUs>60000000||!bounded(e->rate,0,10000)||!flag(e->twoSided)||!bounded(e->nearDistance,.001,1000)||!bounded(e->farDistance,e->nearDistance,10000)||e->nearDistance==e->farDistance||!bounded(e->farFade,0,e->farDistance-e->nearDistance)||!bounded(e->veinContrast,0,1)||!bounded(e->curl,-2,2)||!bounded(e->backTint,0,1))return 0;
        if(!e->id||e->id>65535||nrEffectFamily(e->effect)!=0||e->count<0||e->count>100000||e->born<0||e->born>(e->rate>0||s->flowSprays[i].flowId?1000000000:e->count*e->cycles)||!materialRef(e->material)||e->shape<0||e->shape>(s->schema>=NR_STATE_SCHEMA_BIRTH_FRAME?9:4)||!flag(e->schedule)||e->endStyle<0||e->endStyle>5||!flag(e->deposit)||!flag(e->collision)||!flag(e->stopping)||e->topology<0||e->topology>5||e->startUs>86400000000ull||e->runningUs>86400000000ull||e->lifeMinUs<1000||e->lifeMaxUs<e->lifeMinUs||e->lifeMaxUs>3600000000ull||e->tailUs>3600000000ull||e->stopUs>s->timeUs||!vector(e->position,16000)||!vector(e->extent,2000)||!vector(e->velocity,256)||!vector(e->spread,128)||!vector(e->gravity,256)||!vector(e->wind,256)||!vector(e->windVariation,128)||!vector(e->tumble,720)||!vector(e->shapeWeights,1)||!bounded(e->drag,0,30)||!bounded(e->lift,0,20)||!bounded(e->flutterHz,0,30)||!bounded(e->flutterAmount,0,10)||!bounded(e->sizeMin,.005,64)||!bounded(e->sizeMax,e->sizeMin,64)||!bounded(e->alpha,0,1)||!bounded(e->heat,0,64)||!bounded(e->radius,.1,200)||!bounded(e->windScale,.1,1000)||!bounded(e->windPeriod,.1,120)||e->birthFadeUs>60000000||e->deathFadeUs>60000000||e->trailUs>2000000||e->coreUs>10000000)return 0;
    }
    for(int i=0; i<(int)NR_MAX_PARTICLES; i++) {
        const Particle*p=&s->particles[i];
        if(!particleMotionValid(s->particleMotions[i].orientation,s->particleMotions[i].angularVelocity,s->particleMotions[i].authored,s->particleMotions[i].padding))return 0;
        if(p->state<0||p->state>2)return 0;
        if(!p->state)continue;
        if(p->leafShape<0||p->leafShape>2)return 0;
        if(!p->id||p->id>=s->nextParticle||p->emitterSlot<0||p->emitterSlot>=(int)NR_MAX_EMITTERS||!s->emitters[p->emitterSlot].used||p->emitterId!=s->emitters[p->emitterSlot].id||nrEffectFamily(p->effect)!=0||!materialRef(p->material)||p->bornStep>s->step||!p->lifeSteps||p->lifeSteps>432000||!bounded(p->size,.005,64)||!bounded(p->angle,0,360)||!bounded(p->heat,0,1))return 0;
    }
    for(int i=0; i<NR_DEPOSITS; i++) {
        const Deposit*d=&s->deposits[i];
        if(d->used&&(d->sampling<0||d->sampling>3||!bounded(d->surfaceAlpha,0,1)))return 0;
        if(!flag(d->used))return 0;
        if(d->used&&(d->leafShape<0||d->leafShape>2||!bounded(d->veinContrast,0,1)||!bounded(d->curl,-2,2)||!bounded(d->backTint,0,1)))return 0;
        if(d->used&&(!d->id||d->id>=s->nextParticle||!d->emitterId||d->emitterId>65535||!d->emitterGeneration||d->emitterGeneration>s->nextEmitterGeneration||nrEffectFamily(d->effect)!=0||!materialRef(d->material)||!vector(d->position,32760)||!bounded(d->size,.005,64)||!bounded(d->angle,0,360)||!bounded(d->alpha,0,1)||d->atUs>s->timeUs))return 0;
    }
    for(int i=0; i<NR_TILES; i++) {
        const DepositTile*t=&s->tiles[i];
        if(!flag(t->used)||t->color>0xffffffu)return 0;
        if(t->used&&(t->x< -327600||t->x>327600||t->z< -327600||t->z>327600||!t->count||t->atUs>s->timeUs))return 0;
    }
    for(int i=0; i<NR_FIELDS; i++) {
        const Field*v=&s->fields[i];
        if(!flag(v->used))return 0;
        if(v->used&&(nrEffectFamily(v->effect)!=1||!materialRef(v->material)||v->atUs>s->timeUs||v->lifeUs>60000000||!bounded(v->x,NR_LAYOUT_MIN,NR_LAYOUT_MAX)||!bounded(v->y,NR_LAYOUT_MIN,NR_LAYOUT_MAX)||!bounded(v->width,.05,NR_LAYOUT_MAX)||!bounded(v->speed,0,100)||!bounded(v->strength,0,1)))return 0;
    }
    for(int i=0; i<NR_MATERIALS; i++) {
        const Material*m=&s->materials[i];
        if(!flag(m->used))return 0;
        if(!m->used)continue;
        if(m->space<0||m->space>7||!flag(m->scope)||m->blend<0||m->blend>27||m->gradientCount<0||m->gradientCount>16||m->colorCount<0||m->colorCount>64||(m->space==7&&!m->colorCount)||!track(&m->alpha)||!track(&m->index)||!bounded(m->hueStep,-360,360)||!bounded(m->spacing,-100,100))return 0;
        for(int k=0; k<4; k++)if(!track(&m->channel[k]))return 0;
        for(int k=0; k<m->gradientCount; k++)for(int j=0; j<4; j++)if(!bounded(m->stops[k][j],-10000,10000))return 0;
        for(int k=0; k<m->colorCount; k++)if(m->colors[k]>0xffffffu)return 0;
    }
    for(int i=0; i<NR_TEXTS; i++) {
        const TextRun*t=&s->text[i];
        if(!flag(t->used))return 0;
        uint32_t phaseModel=s->textPhaseModel[i];
        if(phaseModel>3||(phaseModel&&(!t->used||s->schema<NR_STATE_SCHEMA_TEXT_PHASE_MODEL||(phaseModel==3?0:!nrTextSupportsPhaseModel(t->effect)))))return 0;
        int alphabetCapacity=s->schema>=NR_STATE_SCHEMA_TEXT_ALPHABET?256:128;
        if(t->used&&(t->alphabetCount<1||t->alphabetCount>alphabetCapacity))return 0;
        for(int k=0;k<128;k++){
            uint32_t g=s->textAlphabetTail[i][k];int active=t->used&&k+128<t->alphabetCount;
            if(!active){if(g)return 0;}else if(g<32||(g>=127&&g<=159)||(g>=0xd800&&g<=0xdfff)||g>0x10ffff)return 0;
        }
        if(!t->used)continue;
        for(int k=0;k<t->alphabetCount&&k<128;k++){uint32_t g=t->alphabet[k];if(g<32||(g>=127&&g<=159)||(g>=0xd800&&g<=0xdfff)||g>0x10ffff)return 0;}
        if(t->count<0||t->count>(int)NR_MAX_TEXT)return 0;
        if(t->delayUs>60000000||t->totalUs>86400000000ull||!flag(t->reverseOrder)||!flag(t->randomOrder)||!flag(t->retargeted)||t->trailLength<0||t->trailLength>8)return 0;
        for(int k=0;k<t->count;k++)if(t->rank[k]>=t->count||t->column[k]>=t->width||t->row[k]>NR_MAX_TEXT||!bounded(t->origin[k].dx,-1000000,1000000)||!bounded(t->origin[k].dy,-1000000,1000000)||!bounded(t->origin[k].da,-1,1)||!bounded(t->origin[k].dh,-2000000,2000000)||!t->origin[k].identity||t->origin[k].identity>s->nextGlyphIdentity)return 0;
        if(t->id<1||t->id>65535||nrEffectFamily(t->effect)!=2||!flag(t->phase)||!flag(t->local)||t->width<1||!materialRef(t->material)||t->easing<0||t->easing>9||t->batchSize<1||t->batchSize>128||!glyphs(t->text,t->count,NR_MAX_TEXT)||!glyphs(t->alphabet,t->alphabetCount<128?t->alphabetCount:128,128)||t->alphabetCount<1||t->startUs>s->timeUs||t->durationUs>60000000||t->staggerUs>10000000||t->jitterUs>10000000||!bounded(t->distance,0,100)||!bounded(t->scatter,0,120)||!bounded(t->variation,0,2)||!bounded(t->wind,-100,100)||!bounded(t->overshoot,0,3)||!bounded(t->cycles,0,50)||!bounded(t->scrambleHz,0,120)||!bounded(t->hueSpread,-360,360))return 0;
    }
    for(int i=0; i<(int)NR_MAX_WINDOWS; i++) {
        const Window*w=&s->windows[i];
        if(s->schema<NR_STATE_SCHEMA_WINDOW_POOLS&&i>=12&&w->used)return 0;
        if(!flag(w->used)||s->windowSourceGeometry[i]>1||(!w->used&&s->windowSourceGeometry[i])||(s->schema<NR_STATE_SCHEMA_WINDOW_SOURCE&&s->windowSourceGeometry[i]))return 0;
        if(w->used&&(!bounded(w->anchorX,-2,3)||!bounded(w->anchorY,-2,3)||!bounded(w->overshoot,0,1)||!bounded(w->scatter,0,100)||!bounded(w->bend,-40,40)||w->folds<1||w->folds>32||w->meshColumns<2||w->meshColumns>32||w->meshRows<2||w->meshRows>24||w->polygonCount<0||w->polygonCount>32||(w->shape==11&&w->polygonCount<3)))return 0;
        if(w->polygonCount<0||w->polygonCount>32)return 0;
        for(int k=0;k<w->polygonCount;k++)if(!bounded(w->polygon[k][0],0,1)||!bounded(w->polygon[k][1],0,1))return 0;
        if(w->used&&(w->padding<0||w->padding>8||w->border<0||w->border>4||w->chromeSize<1||w->chromeSize>5||w->minColumns<=2*(w->padding+1)||!bounded(w->fadeStartRatio,.001,8)||!bounded(w->fadeEndRatio,0,8)||w->fadeEndRatio>=w->fadeStartRatio))return 0;
        if(w->used&&(!flag(w->reader)||w->scrollRow<0||w->scrollRow>(int)NR_MAX_TEXT||w->minColumns<8||w->maxColumns<w->minColumns))return 0;
        if(w->used&&(w->id<1||w->id>65535||nrEffectFamily(w->effect)!=3||w->shape<0||w->shape>11||!materialRef(w->material)||!flag(w->target)||!flag(w->maximized)||!glyphs(w->title,w->titleCount,160)||!glyphs(w->text,w->textCount,NR_MAX_TEXT)||w->atUs>s->timeUs||w->durationUs>60000000||!bounded(w->fromVisibility,0,1)||!bounded(w->alpha,0,1)||!bounded(w->width,1,NR_LAYOUT_MAX)||!bounded(w->height,1,NR_LAYOUT_MAX)||!vector(w->position,16000)||!bounded(w->yaw,-36000,36000)||!bounded(w->pitch,-36000,36000)||!bounded(w->roll,-36000,36000)))return 0;
    }
    for(int i=0; i<NR_WIDGETS; i++)if(!nrValidWidget(s,&s->widgets[i]))return 0;
    for(int i=0; i<NR_AREAS; i++) {
        const Area*a=&s->areas[i];
        if(!flag(a->used))return 0;
        if(a->used&&(a->layout<0||a->layout>2||a->availableUs>86460000000ull))return 0;
        if(a->used&&(a->id<1||a->id>65535||a->parent<0||a->parent>65535||a->width<1||a->height<1||a->padding<0||a->padding>8||a->margin<0||a->margin>8||a->border<0||a->border>4||!flag(a->hideEmpty)||!materialRef(a->material)||!bounded(a->alpha,0,1)||!bounded(a->speedX,-100,100)||!bounded(a->speedY,-30,30)||a->fadeUs>60000000||a->gapUs>60000000))return 0;
    }
    for(int i=0; i<NR_MESSAGES; i++) {
        const Message*m=&s->messages[i];
        if(!flag(m->used))return 0;
        if(m->used) {
            if(!string(m->key,sizeof(m->key))||m->coalesce<0||m->coalesce>2||
               !flag(m->important)||!flag(m->acknowledged)||!m->occurrences||
               (m->coalesce&&(!m->key[0]||m->important))||m->actionCount<0||m->actionCount>NR_NOTIFICATION_ACTIONS||
               (m->actionMask>>m->actionCount))return 0;
            for(int a=0;a<m->actionCount;a++) {
                const NotificationAction*n=&m->actions[a];
                if(n->id<1||n->id>65535||!flag(n->dismiss)||n->labelCount<1||
                   !glyphs(n->label,n->labelCount,NR_ACTION_LABEL)||!string(n->event,sizeof(n->event))||
                   !nrEventPath(n->event)||!bounded(n->value,-1000000,1000000))return 0;
                for(int b=0;b<a;b++)if(n->id==m->actions[b].id)return 0;
            }
        }
        if(m->used&&(m->state<0||m->state>3||m->x<0||m->y<0||m->readyUs>86400000000ull||!m->sequence||m->sequence>s->nextMessage))return 0;
        if(m->used&&(m->id<1||m->id>65535||m->area<0||m->area>65535||m->mode<0||m->mode>6||m->priority<0||m->priority>100||!glyphs(m->text,m->count,NR_MAX_TEXT)||m->startUs>86400000000ull||m->durationUs>86400000000ull))return 0;
    }
    if(s->nextMessageId<1||s->nextMessageId>65536||s->nextIntent<1||s->nextIntent>9007199254740992ull)return 0;
    for(int i=0;i<NR_INTENTS;i++) {
        const Intent*q=&s->intents[i];if(!flag(q->used))return 0;if(!q->used)continue;
        if(!q->id||q->id>=s->nextIntent||q->atUs>s->timeUs||
           !string(q->event,sizeof(q->event))||!nrEventPath(q->event)||!bounded(q->value,-1000000,1000000))return 0;
        if(!q->messageId){if(s->schema<NR_STATE_SCHEMA_GENERAL_API||q->actionId||q->messageSequence)return 0;}
        else if(q->messageId<1||q->messageId>65535||q->actionId<1||q->actionId>65535||!q->messageSequence||q->messageSequence>s->nextMessage)return 0;
        for(int k=0;k<i;k++)if(s->intents[k].used&&s->intents[k].id==q->id)return 0;
    }
    for(int i=0; i<NR_INDICATORS; i++) {
        const Indicator*a=&s->indicators[i];
        if(!flag(a->used))return 0;
        if(a->used&&(a->id<1||a->id>65535||a->area<0||a->area>65535||!glyphs(a->glyphs,a->count,128)||a->count<1||!materialRef(a->material)||!flag(a->cursor)||a->stepUs<1||a->stepUs>60000000))return 0;
    }
    for(int i=0; i<(int)NR_MAX_NODES; i++)if(!nrValidNode(s,&s->nodes[i]))return 0;
    if(s->selectionScroll<0||s->selectionScroll>8192)return 0;
    if(s->edgeCount<0||s->edgeCount>NR_EDGES||s->meshCount<0||s->meshCount>NR_MESH||s->dimensions<2||s->dimensions>3||s->layoutMode<0||s->layoutMode>2)return 0;
    for(int i=0; i<s->edgeCount; i++)if(nrFindNode(s,s->edges[i].from)<0||nrFindNode(s,s->edges[i].to)<0||s->edges[i].kind<0||s->edges[i].kind>5)return 0;
    for(int i=0; i<s->meshCount; i++) {
        const Triangle*t=&s->mesh[i];
        if(!vector(t->a,16000)||!vector(t->b,16000)||!vector(t->c,16000)||t->color>0xffffffu||!bounded(t->alpha,0,1))return 0;
        Vec3 normal=nrCross(nrSub(t->b,t->a),nrSub(t->c,t->a));
        if(nrDot(normal,normal)<=1e-16)return 0;
    }
    for(int i=0; i<NR_VALUES; i++) {
        const Value*v=&s->values[i];
        if(!flag(v->used))return 0;
        if(v->used&&s->schema<NR_STATE_SCHEMA_WIDE_UNBOUND_VALUES&&!v->bindingFamily&&!bounded(v->value,-1000000,1000000))return 0;
        if(v->used&&(!flag(v->readonly)||!string(v->path,sizeof(v->path))||v->path[0]!='/'||!string(v->field,sizeof(v->field))||!nrValueNumberValid(v,v->value)||v->bindingFamily<0||v->bindingFamily>24||!nrResourceBindingShapeValid(v)||
           (s->schema<NR_STATE_SCHEMA_RESOURCE_ANIMATION&&(v->bindingFamily==24||(v->bindingFamily==2&&nrBurstBindingField(v->field))))||
           (s->schema<NR_STATE_SCHEMA_GENERAL_API&&!nrLegacyBindingShapeValid(v))||
           (s->schema<NR_STATE_SCHEMA_COLOR_FIELDS&&v->bindingFamily==14&&strcmp(v->field,"x")&&strcmp(v->field,"y")&&strcmp(v->field,"width")&&strcmp(v->field,"speed")&&strcmp(v->field,"strength")&&strcmp(v->field,"lifeMs")&&strcmp(v->field,"material"))||
           (s->schema<NR_STATE_SCHEMA_FLOAT_HULLS&&v->bindingFamily==18&&!strncmp(v->field,"hull.",5))||
           (s->schema<NR_STATE_SCHEMA_THERMAL_SETTINGS&&v->bindingFamily==21&&!strncmp(v->field,"thermal.",8))||
           (s->schema<NR_STATE_SCHEMA_WATER_SETTINGS&&v->bindingFamily==16&&!strncmp(v->field,"water.",6))||
           (s->schema<NR_STATE_SCHEMA_FLOW_SETTINGS&&v->bindingFamily==16&&(!strcmp(v->field,"thickness.width")||!strcmp(v->field,"thickness.speed")))||
           (s->schema<NR_STATE_SCHEMA_FOAM_TRANSPORT&&v->bindingFamily==19&&(!strcmp(v->field,"velocity.x")||!strcmp(v->field,"velocity.z")))||
           (v->bindingFamily!=14&&(v->bindingId<0||v->bindingId>65535))))return 0;
        if(v->used)for(int k=0;k<i;k++)if(s->values[k].used&&!strcmp(v->path,s->values[k].path))return 0;
    }
    for(int i=0; i<NR_TRIGGERS; i++) {
        const Trigger*t=&s->triggers[i];
        if(!flag(t->used))return 0;
        if(t->used&&(t->id<1||t->id>65535||t->target<0||t->target>=NR_VALUES||
           !s->values[t->target].used||s->values[t->target].readonly||!nrValidConditions(s,t)||
           (t->source < -2 || t->source >= NR_VALUES) ||
           (t->source == NR_TRIGGER_SOURCE_INTENT_VALUE && ((s->schema<NR_STATE_SCHEMA_GENERAL_API && s->schema != NR_STATE_SCHEMA_CELL_ART && s->schema != NR_STATE_SCHEMA_THERMAL_LINK && s->schema != NR_STATE_SCHEMA_THERMAL_TRANSFER && s->schema != NR_STATE_SCHEMA_THERMAL && s->schema != NR_STATE_SCHEMA_WATER_REEMIT && s->schema != NR_STATE_SCHEMA_WATER_LINK && s->schema != NR_STATE_SCHEMA_WATER_TRANSFER && s->schema != NR_STATE_SCHEMA_SURFACE_WATER && s->schema != NR_STATE_SCHEMA_SPRAY_PARTICLES && s->schema != NR_STATE_SCHEMA_FLOW_SPRAY && s->schema != NR_STATE_SCHEMA_FLOW_SINK && s->schema != NR_STATE_SCHEMA_FLOW_SURFACE && s->schema != NR_STATE_SCHEMA_FLOW && s->schema != NR_STATE_SCHEMA_REPEAT_EDIT && s->schema != NR_STATE_SCHEMA_EDITOR_REDO && s->schema != NR_STATE_SCHEMA_NAMED_REGISTERS && s->schema != NR_STATE_SCHEMA_VIM_REGISTER && s->schema != NR_STATE_SCHEMA_VIM_OPERATOR && s->schema != NR_STATE_SCHEMA_VIM_COUNT && s->schema != NR_STATE_SCHEMA_PATH_ACTORS && s->schema != NR_STATE_SCHEMA_FOAM && s->schema != NR_STATE_SCHEMA_FLOAT_BODIES && s->schema != NR_STATE_SCHEMA_SURFACE_WAVES && s->schema != NR_STATE_SCHEMA_PARTICLE_MOTION && s->schema != NR_STATE_SCHEMA_BIRTH_FRAME && s->schema != NR_STATE_SCHEMA_GEOMETRY && s->schema != NR_STATE_SCHEMA_PRE_GEOMETRY && s->schema != NR_STATE_SCHEMA_LOCAL_ACTION) || !t->eventPath[0] || t->action < 0 || t->action > 1)) ||
           t->edge<0||t->edge>3||!flag(t->action)||!flag(t->lastTruth)||!flag(t->pending)||!flag(t->hasFired)||!flag(t->pendingTruth)||
           !bounded(t->value,-1000000,1000000)||t->debounceUs>86400000000ull||t->cooldownUs>86400000000ull||
           t->pendingUs>s->timeUs||t->lastFireUs>s->timeUs||!string(t->eventPath,sizeof(t->eventPath))||
           (t->eventPath[0]&&(!nrEventPath(t->eventPath)||t->edge!=0))||t->lastIntent>=s->nextIntent||t->pendingIntent>=s->nextIntent))return 0;
    }
    if(s->background>0xffffffu||s->stars<0||s->stars>2000||s->sampling<0||s->sampling>3||s->style<0||s->style>5||!bounded(s->starFar,20,1000)||!flag(s->pointerActive)||s->pointerKind<0||s->pointerKind>3||!bounded(s->pointerX,-2147483647.0/2,2147483647.0/2)||!bounded(s->pointerY,-2147483647.0/4,2147483647.0/4))return 0;
    if(!occlusionControlsValid(&s->occlusionControls))return 0;
    if(!nrValidStyles(s)||!nrValidGeometry(s)||!nrValidTriggerFormulas(s)||!nrIntentPayloadStorageValid(s))return 0;
    return 1;
}
