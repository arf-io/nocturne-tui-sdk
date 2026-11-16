#include "internal.h"
static int materialValue(const State*s,double x) {return x>=0&&x<NR_MATERIALS&&(int)x==x&&s->materials[(int)x].used;}
static int flagValue(double x) {return x==0||x==1;}
static int milliseconds(double x,uint64_t*out){double us=x*1000;if(us<0||us>60000000||us!=(uint64_t)us)return 0;*out=(uint64_t)us;return 1;}
int nrValueNumberValid(const Value*v,double x){
    if(!v->bindingFamily)return x>=-1e12&&x<=1e12;
    if(v->bindingFamily==18&&!strncmp(v->field,"hull.",5))return nrFloatHullNumberValid(v,x);
    if(v->bindingFamily==16&&!strncmp(v->field,"water.",6)){
        if(!strcmp(v->field,"water.capacity"))return x>0&&x<=1000000;
        return !strcmp(v->field,"water.evaporationUs")&&x>=0&&x<=86400000000.0&&x==(uint64_t)x&&(x==0||x>=1000);
    }
    if(v->bindingFamily==21&&!strncmp(v->field,"thermal.",8)){
        if(!strcmp(v->field,"thermal.power"))return x>=-1000000&&x<=1000000;
        if(!strcmp(v->field,"thermal.ambientTemperature"))return x>=0&&x<=10000;
        return !strcmp(v->field,"thermal.conductance")&&x>=0&&x<=1000000;
    }
    if(v->bindingFamily==16&&(!strcmp(v->field,"thickness.width")||!strcmp(v->field,"thickness.speed")))return x>=.000001&&x<=10000;
    if(v->bindingFamily==24&&(!strcmp(v->field,"delayMs")||!strcmp(v->field,"holdMs")||!strcmp(v->field,"fadeMs")||!strcmp(v->field,"repeatMs")))return x>=0&&x<=86400000&&x*1000==(uint64_t)(x*1000);
    if(v->bindingFamily==23)return flagValue(x);
    if(x>=-1000000&&x<=1000000)return 1;
    int family=v->bindingFamily;
    if((family==18||family==19||family==20||family==21)&&!strcmp(v->field,"color"))return x>=0&&x<=0xffffff;
    if(family==16&&!strcmp(v->field,"heatColor"))return x>=0&&x<=0xffffff;
    if(family==16&&!strcmp(v->field,"retentionMs"))return x>=0&&x<=86400000;
    if(family==1){const char*suffix=strrchr(v->field,'.');
        if(suffix&&!strcmp(suffix,".seed"))return x>=0&&x<=4294967295.0;
        if(suffix&&!strcmp(suffix,".periodMs"))return x>0&&x<=3600000;
    }
    if(family==12&&(!strcmp(v->field,"minRows")||!strcmp(v->field,"maxRows")))return x>=1&&x<=NR_LAYOUT_MAX;
    if(family==13&&!strcmp(v->field,"background"))return x>=0&&x<=0xffffff;
    if(family==10&&!strcmp(v->field,"color"))return x>=0&&x<=0xffffff;
    if(family==10&&(!strcmp(v->field,"minColumns")||!strcmp(v->field,"maxColumns")))return x>=8&&x<=NR_LAYOUT_MAX;
    if(family==2&&(!strcmp(v->field,"runningTimeMs")||!strcmp(v->field,"lifetimeMinMs")||!strcmp(v->field,"lifetimeMaxMs")||!strcmp(v->field,"tailMs")))return x>=0&&x<=86400000;
    if(family==8&&!strcmp(v->field,"retentionMs"))return x>=0&&x<=86400000;
    if(family!=3&&family!=5&&family!=6&&family!=7&&family!=11&&family!=14&&family!=22)return 0;
    if(!strcmp(v->field,"width")||!strcmp(v->field,"height")||
       (family!=5&&(!strcmp(v->field,"x")||!strcmp(v->field,"y")))||
       (family==5&&(!strcmp(v->field,"minColumns")||!strcmp(v->field,"maxColumns"))))return x>=NR_LAYOUT_MIN&&x<=NR_LAYOUT_MAX;
    return 0;
}
int nrBindValue(State*s,const Value*v,double x) {
    if(s->schema<NR_STATE_SCHEMA_WIDE_UNBOUND_VALUES&&!v->bindingFamily&&!(x>=-1000000&&x<=1000000))return 0;
    if(!nrValueNumberValid(v,x))return 0;
    if(!v->bindingFamily)return 1;
    if(v->bindingFamily==24)return nrBindElectricalValue(s,v,x);
    if(v->bindingFamily==22)return nrBindCellArtValue(s,v,x);
    if(v->bindingFamily==21&&!strncmp(v->field,"thermal.",8))return nrBindThermalValue(s,v,x);
    if(v->bindingFamily==20||v->bindingFamily==21)return nrBindMeshAppearance(s,v,x);
    if(v->bindingFamily==19)return nrBindFoamValue(s,v,x);
    if(v->bindingFamily==18)return nrBindFloatBodyValue(s,v,x);
    if(v->bindingFamily==17)return nrBindWaveValue(s,v,x);
    if(v->bindingFamily==16)return nrBindSurfaceValue(s,v,x);
    if(v->bindingFamily==15)return !strcmp(v->field,"flux")&&nrFlowSetRate(s,(uint32_t)v->bindingId,x);
    if(v->bindingFamily==1)return nrBindMaterialValue(s,v,x);
    if(v->bindingFamily==2)return nrBindEmitterValue(s,v,x);
    if(v->bindingFamily==3) {
        for(int i=0; i<NR_WIDGETS; i++)if(s->widgets[i].used&&s->widgets[i].id==v->bindingId) {
            Widget*w=&s->widgets[i];
            if(!strncmp(v->field,"data.",5)){
                const char*p=v->field+5;int index=0;
                if(*p<'0'||*p>'9'||(*p=='0'&&p[1]))return 0;
                while(*p>='0'&&*p<='9'){index=index*10+(*p++-'0');if(index>=128)return 0;}
                if(*p||index>=w->dataCount||!(x>=-1000000&&x<=1000000))return 0;
                w->data[index]=x;return 1;
            }
#define WINT(name,member,lo,hi) if(!strcmp(v->field,name)){if(x<lo||x>hi||x!=(int)x)return 0;w->member=(int)x;return 1;}
#define WNUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(x<lo||x>hi)return 0;w->member=x;return 1;}
            WINT("x",x,NR_LAYOUT_MIN,NR_LAYOUT_MAX) WINT("y",y,NR_LAYOUT_MIN,NR_LAYOUT_MAX)
            WINT("width",width,1,NR_LAYOUT_MAX) WINT("height",height,1,NR_LAYOUT_MAX)
            WINT("padding",padding,0,8) WINT("mode",mode,0,15)
            WINT("border",border,0,4)
            if(!strcmp(v->field,"sampling")||!strcmp(v->field,"revealMs")){
                if(w->kind<6||w->kind>13)return 0;
                WINT("sampling",sampling,-1,3)
                if(!strcmp(v->field,"revealMs")){if(!milliseconds(x,&w->revealUs))return 0;return 1;}
            }
            if(!strcmp(v->field,"min")){if(x>=w->max)return 0;w->min=x;return 1;}
            if(!strcmp(v->field,"max")){if(x<=w->min)return 0;w->max=x;return 1;}
            if(!strcmp(v->field,"pulseMs")){double us=x*1000;if(us<0||us>60000000||us!=(uint64_t)us)return 0;w->pulseUs=(uint64_t)us;return 1;}
            if(!strcmp(v->field,"cellAspect")||!strcmp(v->field,"startAngle")||!strcmp(v->field,"sweepAngle")){if(w->kind!=8&&w->kind!=9)return 0;}
            if(!strcmp(v->field,"innerRadius")&&w->kind!=9)return 0;
            WNUM("cellAspect",cellAspect,.5,4) WNUM("innerRadius",innerRadius,0,.98)
            WNUM("startAngle",startAngle,-36000,36000) WNUM("sweepAngle",sweepAngle,0,360)
#undef WNUM
#undef WINT
            if(!strcmp(v->field,"alpha")){if(x<0||x>1)return 0;w->alpha=x;return 1;}
            if(!strcmp(v->field,"material")){if(!materialValue(s,x))return 0;w->material=(int)x;return 1;}
            if(!strcmp(v->field,"backgroundMaterial")){if(x!=-1&&!materialValue(s,x))return 0;w->backgroundMaterial=(int)x;return 1;}
            if(!strcmp(v->field,"selected")){if(!flagValue(x))return 0;w->selected=(int)x;return 1;}
            if(!strcmp(v->field,"enabled")){if(!flagValue(x))return 0;w->enabled=(int)x;return 1;}
            if(!strcmp(v->field,"active")){if(!flagValue(x))return 0;w->active=(int)x;return 1;}
            if(strcmp(v->field,"value"))return 0;
            if(w->value!=x)w->changedUs=s->timeUs;
            w->value=x;
            return 1;
        }
        return 0;
    }
    if(v->bindingFamily==4) {
        Camera q=nrCameraAt(s);int matched=0,position=0;
#define CNUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(x<lo||x>hi)return 0;q.member=x;matched=1;}
        CNUM("yaw",yaw,-36000,36000) CNUM("pitch",pitch,-89.9,89.9) CNUM("roll",roll,-36000,36000)
        CNUM("near",nearPlane,.001,100) CNUM("far",farPlane,.01,1000000)
        CNUM("fov",fov,10,150) CNUM("span",span,.1,2000)
        if(!strncmp(v->field,"position.",9)){
            if(x< -16000||x>16000)return 0;
            for(int k=0;k<16;k++)if(s->pathActors[k].used&&!s->pathActors[k].family)return 0;
            if(!strcmp(v->field,"position.x")){q.position.x=x;position=1;}
            if(!strcmp(v->field,"position.y")){q.position.y=x;position=1;}
            if(!strcmp(v->field,"position.z")){q.position.z=x;position=1;}
        }
        if(!strcmp(v->field,"orthographic")){if(!flagValue(x))return 0;q.orthographic=(int)x;matched=1;}
        if((!matched&&!position)||q.nearPlane>=q.farPlane)return 0;
        s->camera=q;memset(&s->flight,0,sizeof(s->flight));nrOriginalCameraStop(s);return 1;
#undef CNUM
    }
    if(v->bindingFamily==5) {
        int i=nrFindWindow(s,v->bindingId);if(i<0)return 0;Window*w=&s->windows[i];
        if(!strcmp(v->field,"alpha")){if(x<0||x>1)return 0;w->alpha=x;if(s->windowPresentation[i].enabled)s->windowPresentation[i].options.opacity=x;return 1;}
        if(!strcmp(v->field,"material")){if(!materialValue(s,x))return 0;w->material=(int)x;return 1;}
        Window q=*w;int matched=0;
#define PNUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(x<lo||x>hi)return 0;q.member=x;matched=1;}
#define PINT(name,member,lo,hi) if(!strcmp(v->field,name)){if(x<lo||x>hi||x!=(int)x)return 0;q.member=(int)x;matched=1;}
        if(!strncmp(v->field,"position.",9)){
            for(int k=0;k<16;k++)if(s->pathActors[k].used&&s->pathActors[k].family==2&&s->pathActors[k].targetId==(uint32_t)w->id)return 0;
        }
        PNUM("position.x",position.x,-16000,16000) PNUM("position.y",position.y,-16000,16000) PNUM("position.z",position.z,-16000,16000)
        PNUM("yaw",yaw,-36000,36000) PNUM("pitch",pitch,-36000,36000) PNUM("roll",roll,-36000,36000)
        PNUM("width",width,1,NR_LAYOUT_MAX) PNUM("height",height,1,NR_LAYOUT_MAX)
        PNUM("anchorX",anchorX,-2,3) PNUM("anchorY",anchorY,-2,3)
        PNUM("overshoot",overshoot,0,1) PNUM("scatter",scatter,0,100) PNUM("bend",bend,-40,40)
        PNUM("fadeStartRatio",fadeStartRatio,.001,8) PNUM("fadeEndRatio",fadeEndRatio,0,8)
        PINT("minColumns",minColumns,8,NR_LAYOUT_MAX) PINT("maxColumns",maxColumns,8,NR_LAYOUT_MAX)
        PINT("padding",padding,0,8) PINT("chromeSize",chromeSize,1,5)
        PINT("border",border,0,4) PINT("group",group,0,65535)
        if(!strcmp(v->field,"shape")){
            if(x<0||x>11||x!=(int)x||(x==11&&q.polygonCount<3))return 0;
            q.shape=(int)x;matched=1;
        }
        PINT("folds",folds,1,32) PINT("meshColumns",meshColumns,2,32) PINT("meshRows",meshRows,2,24)
        if(!strcmp(v->field,"durationMs")){if(!milliseconds(x,&q.durationUs))return 0;matched=1;}
        if(!matched||q.minColumns>q.maxColumns||q.minColumns<=2*(q.padding+1)||q.fadeEndRatio>=q.fadeStartRatio)return 0;
        *w=q;return 1;
#undef PINT
#undef PNUM
    }
    if(v->bindingFamily==6)return nrBindTextValue(s,v,x);
    if(v->bindingFamily==7) {
        for(int i=0;i<NR_AREAS;i++)if(s->areas[i].used&&s->areas[i].id==v->bindingId){Area*a=&s->areas[i];
            if(!strcmp(v->field,"alpha")){if(x<0||x>1)return 0;a->alpha=x;return 1;}
            if(!strcmp(v->field,"material")){if(!materialValue(s,x))return 0;a->material=(int)x;return 1;}
            int matched=0;
#define ANUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(x<lo||x>hi)return 0;a->member=x;matched=1;}
#define AINT(name,member,lo,hi) if(!strcmp(v->field,name)){if(x<lo||x>hi||x!=(int)x)return 0;a->member=(int)x;matched=1;}
            AINT("x",x,NR_LAYOUT_MIN,NR_LAYOUT_MAX) AINT("y",y,NR_LAYOUT_MIN,NR_LAYOUT_MAX) AINT("width",width,1,NR_LAYOUT_MAX) AINT("height",height,1,NR_LAYOUT_MAX)
            AINT("padding",padding,0,8) AINT("margin",margin,0,8) AINT("hideEmpty",hideEmpty,0,1)
            AINT("border",border,0,4) AINT("layout",layout,0,2)
            if(!strcmp(v->field,"parent")){
                if(x<0||x>65535||x!=(int)x)return 0;
                int parent=(int)x;
                for(int depth=0;parent;depth++){
                    if(depth>=NR_AREAS||parent==a->id)return 0;
                    int found=0;
                    for(int z=0;z<NR_AREAS;z++)if(s->areas[z].used&&s->areas[z].id==parent){parent=s->areas[z].parent;found=1;break;}
                    if(!found)return 0;
                }
                a->parent=(int)x;matched=1;
            }
            ANUM("speedX",speedX,-100,100) ANUM("speedY",speedY,-30,30)
            if(!strcmp(v->field,"fadeMs")){if(!milliseconds(x,&a->fadeUs))return 0;matched=1;}
            if(!strcmp(v->field,"gapMs")){if(!milliseconds(x,&a->gapUs))return 0;matched=1;}
            if(matched)nrStatusTick(s);return matched;
#undef AINT
#undef ANUM
        }
        return 0;
    }
    if(v->bindingFamily==8)return nrBindFloorValue(s,v,x);
    if(v->bindingFamily==9) {
        if(strcmp(v->field,"active")||!flagValue(x))return 0;
        for(int i=0;i<NR_REGISTERED_STATES;i++)if(s->registeredStates[i].used&&s->registeredStates[i].id==v->bindingId){s->registeredStates[i].active=(int)x;return 1;}
        return 0;
    }
    if(v->bindingFamily==10)return nrBindNodeValue(s,v,x);
    if(v->bindingFamily==11)return nrBindIndicatorValue(s,v,x);
    if((v->bindingFamily>=12&&v->bindingFamily<=14)||v->bindingFamily==23)return nrBindSceneValue(s,v,x);
    return 0;
}
/* All rules read the same pre-write value set. Their actions are bounded and
 * ordered by stable registration slot; no recursive trigger cascades occur.
 */
int nrValuesTick(NrContext*c,State*s) {
    /* Import validates queued command structure and its direct writes, not the
     * availability of future trigger/style effects. A host may have introduced
     * a repairable action/guard fault after registering the pending input.
     * Registration and real execution still evaluate every consumer normally;
     * nrValidState independently validates retained trees after the probe. */
    if(c->checkingPending&&s==&c->probe)return 1;
    double before[NR_VALUES];
    for(int i=0;i<NR_VALUES;i++)before[i]=s->values[i].value;
    int hasData=0;for(int i=0;i<NR_TRIGGERS;i++)if(s->triggerDataFormulas[i].tree.count||s->triggerGuardFormulas[i].tree.count)hasData=1;
    if(hasData)memcpy(c->typedBefore,s->typedValues,sizeof(s->typedValues));
    for(int i=0;i<NR_TRIGGERS;i++) {
        Trigger*t=&s->triggers[i];if(!t->used)continue;
        const Intent*candidate=0;uint64_t event=0;
        if(t->eventPath[0]) {
            for(int k=0;k<NR_INTENTS;k++) {
                const Intent*q=&s->intents[k];
                if(q->used&&q->id>t->lastIntent&&!strcmp(q->event,t->eventPath)&&(!event||q->id<event)) {
                    event=q->id;candidate=q;
                }
            }
        }
        int truth;
        if(s->triggerGuardFormulas[i].tree.count){
            if(t->eventPath[0]&&!candidate)truth=0;
            else{IntentPayload result;
                if(!nrEvalDataFormula(c,s,&s->triggerGuardFormulas[i],before,c->typedBefore,candidate,&result))return 0;
                int type=result.tokens[0].type;if(type!=J_TRUE&&type!=J_FALSE)return 0;truth=type==J_TRUE;
            }
        }else truth=nrConditionTruth(t,before,candidate);
        if(t->eventPath[0]) {
            truth=truth&&event!=0;
            if(truth&&(!t->pending||t->pendingIntent!=event)) {
                t->pending=1;t->pendingUs=s->timeUs;t->pendingIntent=event;t->pendingTruth=1;
            }
            if(!truth){t->pending=0;t->pendingIntent=0;}
        } else {
            int edge=t->edge==0?truth&&!t->lastTruth:t->edge==1?!truth&&t->lastTruth:
                t->edge==2?truth!=t->lastTruth:truth&&!t->pending;
            if(edge){t->pending=1;t->pendingUs=s->timeUs;t->pendingTruth=truth;}
            if(t->pending&&truth!=t->pendingTruth)t->pending=0;
        }
        t->lastTruth=truth;
        if(t->pending&&s->timeUs-t->pendingUs>=t->debounceUs&&
           (!t->hasFired||s->timeUs-t->lastFireUs>=t->cooldownUs)) {
            Value*v=&s->values[t->target];
            if(t->source==NR_TRIGGER_SOURCE_INTENT_VALUE&&(!candidate||candidate->id!=t->pendingIntent))return 0;
            if(t->fireCount==0xffffffffu)return 0;
            if(s->triggerDataFormulas[i].tree.count){
                if(s->typedValues[t->target].kind){IntentPayload result;
                    if(!nrEvalDataFormula(c,s,&s->triggerDataFormulas[i],before,c->typedBefore,candidate,&result)||!nrTypedAssign(s,t->target,&result))return 0;
                }else{double operand;
                    if(!nrEvalDataNumber(c,s,&s->triggerDataFormulas[i],before,c->typedBefore,candidate,&operand))return 0;
                    double next=t->action?v->value+operand:operand;if(!nrBindValue(s,v,next))return 0;v->value=next;
                }
            }else{
                double operand=t->source==NR_TRIGGER_SOURCE_INTENT_VALUE?candidate->value:t->value;
                if(s->triggerFormulas[i].count&&!nrEvalTriggerFormula(&s->triggerFormulas[i],before,candidate,candidate?&s->intentPayloads[candidate-s->intents]:0,&operand))return 0;
                double next=t->action?v->value+operand:operand;
                if(!nrBindValue(s,v,next))return 0;v->value=next;
            }
            t->hasFired=1;t->fireCount++;
            t->lastFireUs=s->timeUs;t->pending=0;
            if(t->eventPath[0]){t->lastIntent=t->pendingIntent;t->pendingIntent=0;}
        }
    }
    return nrStylesTick(c,s)&&nrSyncTextIdentities(s);
}

int nrEvaluateValues(NrContext*c,State*s) {
    if(c->deferValues){c->valuesDirty=1;return 1;}
    return nrValuesTick(c,s);
}

/* Compiled slot references must be released before a value slot is reused. */
static int conditionUsesValue(const Trigger*t,int index){
    for(int i=0;i<t->conditionCount;i++)if(t->conditions[i].kind==0&&t->conditions[i].source==index)return 1;return 0;
}
static int fieldEquals(const Json*j,int at,const char*field,const char*path){
    int value=nrField(j,at,field);return value>=0&&nrEqual(j,value,path);
}
static int expressionUsesPath(const Json*j,int at,const char*path,int depth){
    if(at<0||at>=j->count)return 0;
    if(depth>128)return 1; /* Conservative if a future parser admits deeper trees. */
    const JToken*t=&j->tokens[at];
    if(t->type==J_ARRAY){
        for(int child=at+1;child<t->next;child=j->tokens[child].next)
            if(expressionUsesPath(j,child,path,depth+1))return 1;
        return 0;
    }
    if(t->type!=J_OBJECT)return 0;
    if(nrField(j,at,"literal")>=0)return 0;
    if(fieldEquals(j,at,"path",path))return 1;
    int object=nrField(j,at,"object");
    if(object>=0&&j->tokens[object].type==J_OBJECT){
        for(int key=object+1;key<j->tokens[object].next;key=j->tokens[key+1].next)
            if(expressionUsesPath(j,key+1,path,depth+1))return 1;
        return 0;
    }
    for(int key=at+1;key<t->next;key=j->tokens[key+1].next)
        if(expressionUsesPath(j,key+1,path,depth+1))return 1;
    return 0;
}
static int subtreeUsesPath(const Json*j,int at,const char*path){return expressionUsesPath(j,at,path,0);}
static int commandUsesPath(const Json*j,int at,const char*path){
    int op=nrField(j,at,"op");
    if(nrEqual(j,op,"batch")){
        int commands=nrField(j,at,"commands");if(commands<0||j->tokens[commands].type!=J_ARRAY)return 1;
        for(int child=commands+1;child<j->tokens[commands].next;child=j->tokens[child].next)
            if(commandUsesPath(j,child,path))return 1;
        return 0;
    }
    if(nrEqual(j,op,"set"))return fieldEquals(j,at,"path",path)||subtreeUsesPath(j,nrField(j,at,"expression"),path);
    if(nrEqual(j,op,"bind")||nrEqual(j,op,"remove-value"))return fieldEquals(j,at,"path",path);
    if(nrEqual(j,op,"trigger"))return fieldEquals(j,at,"source",path)||fieldEquals(j,at,"target",path)||subtreeUsesPath(j,nrField(j,at,"when"),path)||subtreeUsesPath(j,nrField(j,at,"whenExpression"),path)||subtreeUsesPath(j,nrField(j,at,"expression"),path);
    if(nrEqual(j,op,"style-rule"))return subtreeUsesPath(j,nrField(j,at,"style"),path)||subtreeUsesPath(j,nrField(j,at,"when"),path)||subtreeUsesPath(j,nrField(j,at,"whenExpression"),path);
    return 0;
}
static int triggerUsesValue(const State*s,int i,int index){
    if(s->triggers[i].used){
        const NumericFormula*f=&s->triggerFormulas[i];
        for(int k=0;k<f->count;k++)if(f->nodes[k].kind==1&&f->nodes[k].ref==index)return 1;
        const DataFormula*data[]={&s->triggerDataFormulas[i],&s->triggerGuardFormulas[i]};
        for(int n=0;n<2;n++)for(int k=0;k<data[n]->tree.count;k++)if((data[n]->tree.nodes[k].kind==1||data[n]->tree.nodes[k].kind==11||data[n]->tree.nodes[k].kind==101)&&data[n]->tree.nodes[k].ref==index)return 1;
        if(s->triggers[i].target==index||conditionUsesValue(&s->triggers[i],index))return 1;
    }return 0;
}
static int styleUsesValue(const State*s,int i,int index){
    if(s->styleRules[i].used){
        const StyleRule*r=&s->styleRules[i];if(conditionUsesValue(&r->guard,index))return 1;
        const NumericFormula*f=&s->styleGuardFormulas[i].tree;
        for(int k=0;k<f->count;k++)if((f->nodes[k].kind==1||f->nodes[k].kind==11||f->nodes[k].kind==101)&&f->nodes[k].ref==index)return 1;
        for(int k=0;k<NR_STYLE_PROPERTIES;k++)if((r->propertyMask&(1u<<k))&&r->properties[k].mapped&&r->properties[k].source==index)return 1;
    }return 0;
}
int nrValueInUse(NrContext*c,const State*s,int index){
    for(int i=0;i<NR_TRIGGERS;i++)if(triggerUsesValue(s,i,index))return 1;
    for(int i=0;i<NR_STYLE_RULES;i++)if(styleUsesValue(s,i,index))return 1;
    /* Queued consumers retain paths, not compiled slots. Do not confuse a
     * selector/component path with the separate numeric ValueStore namespace. */
    for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used){
        if(s->pending[i].id==c->executingPendingId)continue;
        const PendingCommand*p=&s->pending[i];Json*j=&c->repeatJson;const char*path=s->values[index].path;
        if(!nrParse(j,p->command,p->length)||commandUsesPath(j,0,path))return 1;
    }return 0;
}
/* This operates only on an import probe. It models explicit host retirement of
 * blockers, so subsequent replacement children can be validated normally. */
void nrProbeReleaseValueConsumers(NrContext*c,State*s,const char*path){
    if(!c->checkingPending||s!=&c->probe)return;
    int index=-1;for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&!strcmp(s->values[i].path,path)){index=i;break;}
    if(index<0)return;
    for(int i=0;i<NR_TRIGGERS;i++)if(triggerUsesValue(s,i,index)){
        memset(&s->triggers[i],0,sizeof(Trigger));memset(&s->triggerFormulas[i],0,sizeof(NumericFormula));
        memset(&s->triggerDataFormulas[i],0,sizeof(DataFormula));memset(&s->triggerGuardFormulas[i],0,sizeof(DataFormula));
    }
    for(int i=0;i<NR_STYLE_RULES;i++)if(styleUsesValue(s,i,index)){
        memset(&s->styleRules[i],0,sizeof(StyleRule));memset(&s->styleGuardFormulas[i],0,sizeof(DataFormula));
    }
    for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used&&s->pending[i].id!=c->executingPendingId){
        PendingCommand*p=&s->pending[i];
        if(nrParse(&c->repeatJson,p->command,p->length)&&commandUsesPath(&c->repeatJson,0,path))memset(p,0,sizeof(*p));
    }
}
