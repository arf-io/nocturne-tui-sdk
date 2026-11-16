#include "internal.h"
/* Registered selectors are compiled data, not executable expressions. Resolution
 * reads authoritative state and writes only a caller-owned presentation copy. */
static const char *const FAMILY_NAMES[] = {
    "", "widget", "window", "emitter", "text", "area", "indicator", "node", "floor", "mesh", "prompt", "electrical-arc"
};
static const char *const PROPERTY_NAMES[] = {
    "material", "backgroundMaterial", "alpha", "sampling", "surfaceAlpha", "veinContrast", "color"
};
static const char *const STATE_NAMES[] = {"active", "selected", "hover", "pressed", "disabled"};
static const unsigned FAMILY_PROPERTIES[] = {
    0, 15, 5, 61, 1, 5, 1, 64, 12, 76, 4, 5
};
static const double MINIMUM[] = {0, -1, 0, -1, 0, 0, 0};
static const double MAXIMUM[] = {NR_MATERIALS-1, NR_MATERIALS-1, 1, 3, 1, 1, 0xffffff};
static int fail(NrContext *c, const char *message) {
    size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;
}
static int finiteRange(double value, double low, double high) {return value>=low&&value<=high;}
static int terminated(const char *text, size_t capacity) {
    for(size_t i=0;i<capacity;i++)if(!text[i])return 1;return 0;
}
static int roleValid(const char *role) {
    if(!role[0])return 0;
    for(int i=0;role[i];i++)if(!((role[i]>='a'&&role[i]<='z')||(role[i]>='A'&&role[i]<='Z')||
        (role[i]>='0'&&role[i]<='9')||role[i]=='-'||role[i]=='_'))return 0;
    return 1;
}
static int integerAt(const Json *j,int at,const char *name,int *value,int low,int high,int required) {
    int t=nrField(j,at,name);if(t<0)return !required;double n;
    if(!nrNumber(j,t,&n)||!finiteRange(n,low,high)||(int)n!=n)return 0;*value=(int)n;return 1;
}
static int stringAt(const Json *j,int at,const char *name,char *value,int capacity,int required) {
    int t=nrField(j,at,name);return t<0?!required:nrString(j,t,value,capacity)>=0;
}
static int boolAt(const Json *j,int at,const char *name,int *value) {
    int t=nrField(j,at,name);return t<0||nrBoolean(j,t,value);
}
static int familyAt(const Json *j,int at) {
    int t=nrField(j,at,"family");for(int i=1;i<=NR_STYLE_FAMILIES;i++)if(nrEqual(j,t,FAMILY_NAMES[i]))return i;return 0;
}
static int registryIndex(const State *s,int id) {
    for(int i=0;i<NR_REGISTERED_STATES;i++)if(s->registeredStates[i].used&&s->registeredStates[i].id==id)return i;return -1;
}
static int valueIndex(const State *s,const char *path) {
    for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&!s->typedValues[i].kind&&!strcmp(s->values[i].path,path))return i;return -1;
}
const char *nrStyleFamilyName(int family) {return family>0&&family<=NR_STYLE_FAMILIES?FAMILY_NAMES[family]:"";}
const char *nrStylePropertyName(int property) {return property>=0&&property<NR_STYLE_PROPERTIES?PROPERTY_NAMES[property]:"";}
const char *nrStyleStateName(int state) {return state>=0&&state<NR_STYLE_STATES?STATE_NAMES[state]:"";}

/* Return the original authored properties and whether the target still exists.
 * Registrations become dormant if their object is removed; IDs are not slot indices. */
int nrAuthoredAppearance(const State *s,const RegisteredState *r,Appearance *out) {
    memset(out,0,sizeof(*out));out->mask=FAMILY_PROPERTIES[r->family];int id=r->targetId;
    switch(r->family) {
    case 1:
        for(int i=0;i<NR_WIDGETS;i++){const Widget *w=&s->widgets[i];if(w->used&&w->id==id){out->value[0]=w->material;out->value[1]=w->backgroundMaterial;out->value[2]=w->alpha;out->value[3]=w->sampling;return 1;}}break;
    case 2:{int i=nrFindWindow(s,id);if(i<0)break;out->value[0]=s->windows[i].material;out->value[2]=s->windows[i].alpha;return 1;}
    case 3:{int i=nrFindEmitter(s,id);if(i<0)break;const Emitter *e=&s->emitters[i];out->value[0]=e->material;out->value[2]=e->alpha;out->value[3]=e->sampling;out->value[4]=e->surfaceAlpha;out->value[5]=e->veinContrast;return 1;}
    case 4:for(int i=0;i<NR_TEXTS;i++)if(s->text[i].used&&s->text[i].id==id){out->value[0]=s->text[i].material;return 1;}break;
    case 5:for(int i=0;i<NR_AREAS;i++)if(s->areas[i].used&&s->areas[i].id==id){out->value[0]=s->areas[i].material;out->value[2]=s->areas[i].alpha;return 1;}break;
    case 6:for(int i=0;i<NR_INDICATORS;i++)if(s->indicators[i].used&&s->indicators[i].id==id){out->value[0]=s->indicators[i].material;return 1;}break;
    case 7:{int i=nrFindNode(s,id);if(i<0)break;out->value[6]=s->nodes[i].color;return 1;}
    case 8:out->value[2]=s->floor.alpha;out->value[3]=s->floor.sampling;return 1;
    case 9:
        /* A mesh has per-triangle authored color/alpha. A zero override mask
         * leaves those intact; these aggregate defaults are inspection-only. */
        out->value[2]=s->meshCount?s->mesh[0].alpha:1;out->value[3]=s->meshSampling;
        out->value[6]=s->meshCount?s->mesh[0].color:0;return 1;
    case 10:out->value[2]=s->promptDocument.alpha;return 1;
    case 11:for(int i=0;i<16;i++)if(s->electricalArcs[i].id==(uint32_t)id){out->value[0]=s->electricalArcs[i].material;out->value[2]=s->electricalArcs[i].alpha;return 1;}break;
    }
    out->mask=0;return 0;
}
static int hitMatches(const RegisteredState *r,uint32_t hit) {
    uint32_t family=hit&0xff000000u;int id=(int)(hit&0xffffu);
    if(r->family==1)return family==NR_ID_WIDGET&&r->targetId==id;
    if(r->family==2)return (family==NR_ID_WINDOW||family==NR_ID_DOCK||family==NR_ID_CLOSE||family==NR_ID_MIN||family==NR_ID_MAX||family==NR_ID_WINDOW_RETURN)&&r->targetId==id;
    if(r->family==7)return family==NR_ID_NODE&&r->targetId==id;
    if(r->family==10)return family==NR_ID_PROMPT;
    return 0;
}
const RegisteredState*nrCharacterRegisteredOwner(const State*s,uint32_t hit){
    if(!hit)return 0;
    for(int i=0;i<NR_REGISTERED_STATES;i++){
        const RegisteredState*r=&s->registeredStates[i];Appearance authored;
        if(r->used&&hitMatches(r,hit)&&nrAuthoredAppearance(s,r,&authored))return r;
    }return 0;
}
const RegisteredState*nrCharacterSemanticOwner(const State*s,uint32_t owner){
    uint32_t family=owner>>16,target=owner&0xffffu;
    if(!family||family>NR_STYLE_FAMILIES)return 0;
    for(int i=0;i<NR_REGISTERED_STATES;i++){
        const RegisteredState*r=&s->registeredStates[i];Appearance authored;
        if(r->used&&r->family==(int)family&&r->targetId==(int)target&&nrAuthoredAppearance(s,r,&authored))return r;
    }return 0;
}
unsigned nrRegisteredFlags(const State *s,const RegisteredState *r) {
    Appearance original;if(!nrAuthoredAppearance(s,r,&original))return 0;
    unsigned flags=1;int id=r->targetId;
    if(r->family==1)for(int i=0;i<NR_WIDGETS;i++)if(s->widgets[i].used&&s->widgets[i].id==id){
        const Widget *w=&s->widgets[i];flags=(w->active?1u:0u)|(w->selected?2u:0u)|(!w->enabled?16u:0u);break;}
    if(r->family==2&&s->selectedWindow==id)flags|=2;
    if(r->family==3){int i=nrFindEmitter(s,id);if(i>=0&&s->emitters[i].stopping)flags&=~1u;}
    if(r->family==7&&s->selection==id)flags|=2;
    if(r->family==10)flags=(s->promptDocument.active?3u:0u);
    if(!r->active)flags&=~1u;
    if(hitMatches(r,s->hoverHit))flags|=4;
    if(hitMatches(r,s->pressedHit))flags|=8;
    return flags;
}
static int selectorTargets(const StateSelector *selector,const RegisteredState *r) {
    if(selector->family!=r->family)return 0;
    if(selector->targetId>=0&&selector->targetId!=r->targetId)return 0;
    if(selector->role[0]&&strcmp(selector->role,r->role))return 0;
    if(selector->path[0]) {
        if(!selector->prefix){if(strcmp(selector->path,r->path))return 0;}
        /* Both paths occupy validated 128-byte arrays; n is at most 127.
         * Bounded memcmp preserves the existing memory-only import contract. */
        else {size_t n=strlen(selector->path);if(memcmp(selector->path,r->path,n)||
             (n>1&&r->path[n]&&r->path[n]!='/'))return 0;}
    }
    return 1;
}
static int ruleMatches(const State *s,const StyleRule *rule,const RegisteredState *r) {
    if(!r->active||!rule->used||!rule->enabled||!rule->guard.lastTruth||!selectorTargets(&rule->selector,r))return 0;
    return (nrRegisteredFlags(s,r)&rule->selector.stateMask)==rule->selector.stateValue;
}
static double mappedValue(const State *s,const StyleValue *value) {
    if(!value->mapped)return value->outputMin;
    double t=nrClamp((s->values[value->source].value-value->inputMin)/(value->inputMax-value->inputMin),0,1);
    return value->outputMin+(value->outputMax-value->outputMin)*t;
}
/* Fill effective properties. Returns the subset actually overridden, so mesh
 * triangles with distinct authored colors are not flattened by unrelated rules. */
unsigned nrEffectiveAppearance(const State *s,const RegisteredState *r,Appearance *out) {
    if(!nrAuthoredAppearance(s,r,out))return 0;
    int priority[NR_STYLE_PROPERTIES];for(int k=0;k<NR_STYLE_PROPERTIES;k++)priority[k]=-32769;
    unsigned changed=0;
    for(int i=0;i<NR_STYLE_RULES;i++) {
        const StyleRule *rule=&s->styleRules[i];if(!ruleMatches(s,rule,r))continue;
        for(int k=0;k<NR_STYLE_PROPERTIES;k++)if((rule->propertyMask&(1u<<k))&&rule->priority>=priority[k]) {
            out->value[k]=mappedValue(s,&rule->properties[k]);priority[k]=rule->priority;changed|=1u<<k;
        }
    }
    return changed;
}
static void applyAppearance(State *s,const RegisteredState *r,const Appearance *p,unsigned mask) {
    if(!mask)return;int id=r->targetId;
    switch(r->family) {
    case 1:for(int i=0;i<NR_WIDGETS;i++)if(s->widgets[i].used&&s->widgets[i].id==id){Widget *w=&s->widgets[i];w->material=(int)p->value[0];w->backgroundMaterial=(int)p->value[1];w->alpha=p->value[2];w->sampling=(int)p->value[3];return;}break;
    case 2:{int i=nrFindWindow(s,id);if(i<0)break;s->windows[i].material=(int)p->value[0];s->windows[i].alpha=p->value[2];break;}
    case 3:{int i=nrFindEmitter(s,id);if(i<0)break;Emitter *e=&s->emitters[i];e->material=(int)p->value[0];e->alpha=p->value[2];e->sampling=(int)p->value[3];e->surfaceAlpha=p->value[4];e->veinContrast=p->value[5];
        /* Airborne particles cache the birth material; update only the scratch
         * particles. Deposits keep the style captured at deposition. */
        if(mask&1u)for(int k=0;k<(int)NR_MAX_PARTICLES;k++)if(s->particles[k].state&&s->particles[k].emitterSlot==i)s->particles[k].material=e->material;
        break;}
    case 4:for(int i=0;i<NR_TEXTS;i++)if(s->text[i].used&&s->text[i].id==id)s->text[i].material=(int)p->value[0];break;
    case 5:for(int i=0;i<NR_AREAS;i++)if(s->areas[i].used&&s->areas[i].id==id){s->areas[i].material=(int)p->value[0];s->areas[i].alpha=p->value[2];}break;
    case 6:for(int i=0;i<NR_INDICATORS;i++)if(s->indicators[i].used&&s->indicators[i].id==id)s->indicators[i].material=(int)p->value[0];break;
    case 7:{int i=nrFindNode(s,id);if(i>=0)s->nodes[i].color=(uint32_t)p->value[6];break;}
    case 8:s->floor.alpha=p->value[2];s->floor.sampling=(int)p->value[3];break;
    case 9:
        if(mask&8u)s->meshSampling=(int)p->value[3];
        for(int i=0;i<s->meshCount;i++){if(mask&4u)s->mesh[i].alpha=p->value[2];if(mask&64u)s->mesh[i].color=(uint32_t)p->value[6];}break;
    case 10:s->promptDocument.alpha=p->value[2];break;
    case 11:for(int i=0;i<16;i++)if(s->electricalArcs[i].id==(uint32_t)id){s->electricalArcs[i].material=(uint32_t)p->value[0];s->electricalArcs[i].alpha=p->value[2];break;}break;
    }
}
void nrPrepareAppearance(NrContext *c) {
    c->rendering=0;int any=0;
    for(int i=0;i<NR_STYLE_RULES;i++)if(c->state.styleRules[i].used&&c->state.styleRules[i].enabled){any=1;break;}
    if(!any)return;
    /* The styled view equals c->state when no registered state takes an override (an enabled rule whose guard,
     * selector or state flags match nothing): render from c->state then, without the 30.5 MB copy
     * (native/docs/TRANSACTIONS.md, section 10). nrEffectiveAppearance reads only c->state. */
    int overridden=0;
    for(int i=0;i<NR_REGISTERED_STATES&&!overridden;i++)if(c->state.registeredStates[i].used){
        Appearance effective;overridden=nrEffectiveAppearance(&c->state,&c->state.registeredStates[i],&effective)!=0;
    }
    if(!overridden)return;
    nrStateCopy(&c->probe,&c->state);c->counters.probeSyncs++;
    for(int i=0;i<NR_REGISTERED_STATES;i++)if(c->state.registeredStates[i].used) {
        Appearance effective;const RegisteredState *r=&c->state.registeredStates[i];
        unsigned mask=nrEffectiveAppearance(&c->state,r,&effective);applyAppearance(&c->probe,r,&effective,mask);
    }
    c->rendering=1;
}
int nrStylesTick(NrContext*c,State*s) {
    double values[NR_VALUES];for(int i=0;i<NR_VALUES;i++)values[i]=s->values[i].value;
    for(int i=0;i<NR_STYLE_RULES;i++)if(s->styleRules[i].used) {
        Trigger*guard=&s->styleRules[i].guard;
        if(s->styleGuardFormulas[i].tree.count){IntentPayload result;
            if(!nrEvalDataFormula(c,s,&s->styleGuardFormulas[i],values,s->typedValues,NULL,&result))return 0;
            int type=result.tokens[0].type;if(type!=J_TRUE&&type!=J_FALSE)return 0;guard->lastTruth=type==J_TRUE;
        }else guard->lastTruth=guard->conditionCount?nrConditionTruth(guard,values,NULL):1;
    }
    return 1;
}
static int parseProperty(const State *s,const Json *j,int at,int index,StyleValue *value) {
    memset(value,0,sizeof(*value));value->source=-1;
    double low=MINIMUM[index],high=MAXIMUM[index];
    if(j->tokens[at].type==J_NUMBER) {
        double v;if(!nrNumber(j,at,&v)||!finiteRange(v,low,high))return 0;
        if((index<2||index==3||index==6)&&(int)v!=v)return 0;
        if(index==3)return 0; /* Sampling is a named policy, not a magic integer. */
        if(index<2&&v>=0&&!s->materials[(int)v].used)return 0;
        value->outputMin=value->outputMax=v;return 1;
    }
    if(index==3) {
        const char *names[]={"inherit","cell","half","braille","hybrid"};
        for(int k=0;k<5;k++)if(nrEqual(j,at,names[k])){value->outputMin=value->outputMax=k-1;return 1;}return 0;
    }
    if(index!=2&&index!=4&&index!=5)return 0;
    if(!nrAllowed(j,at,"path inputMin inputMax outputMin outputMax"))return 0;
    char path[128];if(!stringAt(j,at,"path",path,sizeof(path),1)||(value->source=valueIndex(s,path))<0)return 0;
    const char *names[]={"inputMin","inputMax","outputMin","outputMax"};double *fields[]={&value->inputMin,&value->inputMax,&value->outputMin,&value->outputMax};
    for(int k=0;k<4;k++){int t=nrField(j,at,names[k]);if(t<0||!nrNumber(j,t,fields[k])||!finiteRange(*fields[k],k<2?-1000000:low,k<2?1000000:high))return 0;}
    if(value->inputMin>=value->inputMax)return 0;value->mapped=1;return 1;
}
int nrStyleCommand(NrContext *c,State *s,const Json *j) {
    int op=nrField(j,0,"op"),id=0;
    if(!integerAt(j,0,"id",&id,1,65535,1))return fail(c,"Style or registration id required");
    if(nrEqual(j,op,"state-register")) {
        if(!nrAllowed(j,0,"op id path role target active"))return fail(c,"Unknown state registration parameter");
        RegisteredState record;memset(&record,0,sizeof(record));record.used=record.active=1;record.id=id;
        int target=nrField(j,0,"target");
        if(target<0||!nrAllowed(j,target,"family id")||!(record.family=familyAt(j,target))||
           !integerAt(j,target,"id",&record.targetId,0,65535,1)||((record.family<8||record.family==11)?!record.targetId:record.targetId!=0)||
           !stringAt(j,0,"path",record.path,sizeof(record.path),1)||!nrEventPath(record.path)||
           !stringAt(j,0,"role",record.role,sizeof(record.role),1)||!roleValid(record.role)||!boolAt(j,0,"active",&record.active))
            return fail(c,"Invalid registered path, role or target");
        int slot=registryIndex(s,id);if(slot<0)for(int i=0;i<NR_REGISTERED_STATES;i++)if(!s->registeredStates[i].used){slot=i;break;}
        if(slot<0)return fail(c,"Registered state capacity reached (64)");
        for(int i=0;i<NR_REGISTERED_STATES;i++){const RegisteredState *r=&s->registeredStates[i];if(i!=slot&&r->used&&(!strcmp(r->path,record.path)||(r->family==record.family&&r->targetId==record.targetId)))return fail(c,"Duplicate registered path or target");}
        Appearance original;if(!nrAuthoredAppearance(s,&record,&original))return fail(c,"Registered target does not exist");
        s->registeredStates[slot]=record;return 0;
    }
    if(nrEqual(j,op,"state-update")||nrEqual(j,op,"state-unregister")) {
        int slot=registryIndex(s,id);if(slot<0)return fail(c,"Registered state not found");
        RegisteredState *r=&s->registeredStates[slot];
        if(nrEqual(j,op,"state-unregister")) {if(!nrAllowed(j,0,"op id"))return fail(c,"Unknown unregister parameter");memset(r,0,sizeof(*r));return 0;}
        if(!nrAllowed(j,0,"op id role active")||!stringAt(j,0,"role",r->role,sizeof(r->role),0)||!roleValid(r->role)||!boolAt(j,0,"active",&r->active))return fail(c,"Invalid registered state update");return 0;
    }
    int slot=-1;for(int i=0;i<NR_STYLE_RULES;i++)if(s->styleRules[i].used&&s->styleRules[i].id==id){slot=i;break;}
    if(nrEqual(j,op,"remove-style-rule")) {
        if(!nrAllowed(j,0,"op id")||slot<0)return fail(c,"Style rule not found or invalid removal");memset(&s->styleRules[slot],0,sizeof(StyleRule));memset(&s->styleGuardFormulas[slot],0,sizeof(DataFormula));return 0;
    }
    if(!nrEqual(j,op,"style-rule"))return fail(c,"Unknown style operation");
    if(!nrAllowed(j,0,"op id selector style when whenExpression priority enabled"))return fail(c,"Unknown style rule parameter");
    if(slot<0)for(int i=0;i<NR_STYLE_RULES;i++)if(!s->styleRules[i].used){slot=i;break;}
    if(slot<0)return fail(c,"Style rule capacity reached (32)");
    StyleRule rule;memset(&rule,0,sizeof(rule));rule.id=id;rule.used=rule.enabled=1;rule.selector.targetId=-1;
    int selector=nrField(j,0,"selector"),style=nrField(j,0,"style");
    if(selector<0||!nrAllowed(j,selector,"family id path pathPrefix role states")||!(rule.selector.family=familyAt(j,selector))||
       !integerAt(j,selector,"id",&rule.selector.targetId,0,65535,0)||
       !stringAt(j,selector,"role",rule.selector.role,sizeof(rule.selector.role),0)||
       (rule.selector.role[0]&&!roleValid(rule.selector.role))||
       !integerAt(j,0,"priority",&rule.priority,-32768,32767,0)||!boolAt(j,0,"enabled",&rule.enabled))return fail(c,"Invalid selector family, identity, role or priority");
    if(rule.selector.targetId!=-1&&((rule.selector.family<8||rule.selector.family==11)?rule.selector.targetId<1:rule.selector.targetId!=0))return fail(c,"Selector identity is invalid for family");
    if(nrField(j,selector,"role")>=0&&!rule.selector.role[0])return fail(c,"Selector role cannot be empty");
    int exact=nrField(j,selector,"path"),prefix=nrField(j,selector,"pathPrefix");
    if(exact>=0&&prefix>=0)return fail(c,"Use path OR pathPrefix, not both");
    if(exact>=0||prefix>=0) {
        rule.selector.prefix=prefix>=0;
        if(nrString(j,exact>=0?exact:prefix,rule.selector.path,sizeof(rule.selector.path))<0||
           (!(rule.selector.prefix&&!strcmp(rule.selector.path,"/"))&&!nrEventPath(rule.selector.path)))return fail(c,"Invalid selector path");
    }
    int states=nrField(j,selector,"states");
    if(states>=0) {
        if(!nrAllowed(j,states,"active selected hover pressed disabled"))return fail(c,"Invalid selector state flags");
        for(int i=0;i<NR_STYLE_STATES;i++){int t=nrField(j,states,STATE_NAMES[i]),value=0;if(t<0)continue;if(!nrBoolean(j,t,&value))return fail(c,"Selector states require booleans");rule.selector.stateMask|=1u<<i;if(value)rule.selector.stateValue|=1u<<i;}
    }
    if(style<0||!nrAllowed(j,style,"material backgroundMaterial alpha sampling surfaceAlpha veinContrast color")||!j->tokens[style].count)return fail(c,"Nonempty supported appearance object required");
    for(int k=0;k<NR_STYLE_PROPERTIES;k++){int at=nrField(j,style,PROPERTY_NAMES[k]);if(at<0)continue;
        if(!(FAMILY_PROPERTIES[rule.selector.family]&(1u<<k))||!parseProperty(s,j,at,k,&rule.properties[k]))return fail(c,"Invalid or inapplicable appearance property");
        if(k==3&&rule.selector.family!=1&&rule.properties[k].outputMin<0)return fail(c,"Only widgets support inherited sampling");
        rule.propertyMask|=1u<<k;
    }
    int when=nrField(j,0,"when"),expression=nrField(j,0,"whenExpression");
    if(when>=0&&expression>=0)return fail(c,"Choose condition tree OR typed appearance guard");
    memset(&s->styleGuardFormulas[slot],0,sizeof(DataFormula));
    if(expression>=0){
        if(!nrCompileDataFormula(s,j,expression,&s->styleGuardFormulas[slot])||s->styleGuardFormulas[slot].tree.usesIntent)return fail(c,"Invalid typed appearance guard; event payloads require trigger routing");
        rule.guard.conditionCount=1;rule.guard.conditions[0]=(Condition){.kind=5,.source=-1,.end=1};
    }else if(when>=0&&!nrParseConditions(s,j,when,&rule.guard))return fail(c,"Invalid appearance condition tree");
    rule.guard.lastTruth=when<0&&expression<0;s->styleRules[slot]=rule;return 0;
}
int nrValidStyles(const State *s) {
    for(int i=0;i<NR_REGISTERED_STATES;i++) {
        const RegisteredState *r=&s->registeredStates[i];if(r->used<0||r->used>1)return 0;if(!r->used)continue;
        if(r->id<1||r->id>65535||r->family<1||r->family>NR_STYLE_FAMILIES||(r->family==11&&s->schema<NR_STATE_SCHEMA_RESOURCE_ANIMATION)||r->targetId<0||r->targetId>65535||
           ((r->family<8||r->family==11)?!r->targetId:r->targetId!=0)||r->active<0||r->active>1||!terminated(r->path,sizeof(r->path))||
           !nrEventPath(r->path)||!terminated(r->role,sizeof(r->role))||!roleValid(r->role))return 0;
        for(int k=0;k<i;k++){const RegisteredState *q=&s->registeredStates[k];if(q->used&&(q->id==r->id||!strcmp(q->path,r->path)||(q->family==r->family&&q->targetId==r->targetId)))return 0;}
    }
    for(int i=0;i<NR_STYLE_RULES;i++) {
        const StyleRule *r=&s->styleRules[i];if(r->used<0||r->used>1)return 0;if(!r->used)continue;const StateSelector *p=&r->selector;
        if(r->id<1||r->id>65535||r->enabled<0||r->enabled>1||r->priority< -32768||r->priority>32767||
           p->family<1||p->family>NR_STYLE_FAMILIES||(p->family==11&&s->schema<NR_STATE_SCHEMA_RESOURCE_ANIMATION)||p->targetId< -1||p->targetId>65535||p->prefix<0||p->prefix>1||
           !terminated(p->path,sizeof(p->path))||(p->path[0]&&!(p->prefix&&!strcmp(p->path,"/"))&&!nrEventPath(p->path))||
           !terminated(p->role,sizeof(p->role))||(p->role[0]&&!roleValid(p->role))||p->stateMask>31||(p->stateValue&~p->stateMask)||
           !r->propertyMask||(r->propertyMask&~FAMILY_PROPERTIES[p->family])||r->guard.lastTruth<0||r->guard.lastTruth>1||
           /* Appearance has no event subscription; an event gate would admit intentValue leaves. */
           r->guard.eventPath[0]||r->guard.conditionCount<0||r->guard.conditionCount>NR_CONDITIONS||
           (r->guard.conditionCount&&!nrValidConditions(s,&r->guard)))return 0;
        for(int k=0;k<r->guard.conditionCount;k++)if(r->guard.conditions[k].kind==5&&!s->styleGuardFormulas[i].tree.count)return 0;
        if(p->targetId!=-1&&((p->family<8||p->family==11)?p->targetId<1:p->targetId!=0))return 0;
        /* Leaf-only properties must never be accepted on a rain/snow/ejecta
         * target. Ignore transient guards and flags for applicability: enabling
         * a rule later must not turn a formerly accepted setting into a no-op. */
        if(p->family==3&&(r->propertyMask&48u))for(int k=0;k<NR_REGISTERED_STATES;k++) {
            const RegisteredState *q=&s->registeredStates[k];if(!q->used||!selectorTargets(p,q))continue;
            int at=nrFindEmitter(s,q->targetId);if(at>=0&&nrEffectAlgorithm(s->emitters[at].effect)!=0)return 0;
        }
        for(int n=0;n<i;n++)if(s->styleRules[n].used&&s->styleRules[n].id==r->id)return 0;
        for(int k=0;k<NR_STYLE_PROPERTIES;k++)if(r->propertyMask&(1u<<k)) {
            const StyleValue *v=&r->properties[k];if(v->mapped<0||v->mapped>1||!finiteRange(v->outputMin,MINIMUM[k],MAXIMUM[k])||!finiteRange(v->outputMax,MINIMUM[k],MAXIMUM[k]))return 0;
            if(v->mapped) {
                if((k!=2&&k!=4&&k!=5)||v->source<0||v->source>=NR_VALUES||!s->values[v->source].used||s->typedValues[v->source].kind||
                   !finiteRange(v->inputMin,-1000000,1000000)||!finiteRange(v->inputMax,-1000000,1000000)||v->inputMin>=v->inputMax)return 0;
            } else {
                if(v->source!=-1||v->outputMin!=v->outputMax)return 0;
                if((k<2||k==3||k==6)&&(int)v->outputMin!=v->outputMin)return 0;
                if(k<2&&v->outputMin>=0&&!s->materials[(int)v->outputMin].used)return 0;
                if(k==3&&p->family!=1&&v->outputMin<0)return 0;
            }
        }
    }
    return 1;
}
