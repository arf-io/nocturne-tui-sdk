#include "internal.h"
/* The original numeric table and schema-31 prefix retain their byte layout.
 * Typed data is a separate footer indexed by the same stable value slot. */
static int booleanField(const Value*v){
    const char*field=v->field;
    switch(v->bindingFamily){
        case 2:return !strcmp(field,"twoSided")||!strcmp(field,"collision")||!strcmp(field,"deposit");
        case 3:return !strcmp(field,"enabled")||!strcmp(field,"selected")||!strcmp(field,"active");
        case 4:return !strcmp(field,"orthographic");
        case 6:return !strcmp(field,"local")||!strcmp(field,"reverseOrder")||!strcmp(field,"randomOrder");
        case 7:return !strcmp(field,"hideEmpty");
        case 8:return !strcmp(field,"enabled")||!strcmp(field,"visible");
        case 9:return !strcmp(field,"active");
        case 10:return !strcmp(field,"pinned")||!strcmp(field,"showKind")||!strcmp(field,"showStatus")||!strcmp(field,"showSha")||!strcmp(field,"showDetail");
        case 11:return !strcmp(field,"cursor");
        case 12:return !strcmp(field,"active");
        case 14:return !strcmp(field,"continuous");
        case 19:return !strcmp(field,"enabled");
        case 23:return !strcmp(field,"reducedMotion")||!strcmp(field,"screenReader");
        case 18:return !strcmp(field,"visible");
        case 16:return !strcmp(field,"collisionEnabled")||!strcmp(field,"renderVisible");
        default:return 0;
    }
}
int nrTypedBindingValid(const Value*v,int kind){
    if(!v->bindingFamily)return 1;
    if(kind==1)return booleanField(v);
    if(kind==3)return v->bindingFamily==3&&!strcmp(v->field,"data");
    if(kind!=2)return 0;
    const char*f=v->field;
    return (v->bindingFamily==3&&!strcmp(f,"text"))||
        (v->bindingFamily==5&&(!strcmp(f,"title")||!strcmp(f,"text")))||
        (v->bindingFamily==6&&!strcmp(f,"text"))||
        (v->bindingFamily==11&&!strcmp(f,"sequence"))||
        (v->bindingFamily==10&&(!strcmp(f,"label")||!strcmp(f,"detail")||!strcmp(f,"kind")||!strcmp(f,"status")||!strcmp(f,"sha")));
}
static int glyphString(const IntentPayload*p,uint32_t*out,int cap){
    const JToken*t=&p->tokens[0];int count=nrDecodeSpan(p->json,t->start,t->end,out,cap);
    if(count<0)return -1;for(int i=0;i<count;i++)if(out[i]<32&&out[i]!=10&&out[i]!=9)return -1;
    return count;
}
int nrWidgetDataPayloadValid(const IntentPayload*p){
    if(!p->count||p->count>128||p->tokens[0].type!=J_ARRAY||p->tokens[0].count<0||p->tokens[0].count>128)return 0;
    int token=1;
    for(int k=0;k<p->tokens[0].count;k++){
        if(token>=(int)p->count||p->tokens[token].type!=J_NUMBER||!(p->tokens[token].number>=-1000000&&p->tokens[token].number<=1000000)||p->tokens[token].next!=token+1)return 0;
        token++;
    }return token==(int)p->count;
}
int nrTypedApply(State*s,const Value*v,const TypedValue*t){
    if(!nrTypedBindingValid(v,t->kind))return 0;
    if(!v->bindingFamily)return 1;
    if(t->kind==1)return nrBindValue(s,v,t->data.tokens[0].type==J_TRUE?1:0);
    if(t->kind==3){
        const IntentPayload*p=&t->data;if(!nrWidgetDataPayloadValid(p))return 0;
        double values[128];int count=p->tokens[0].count,token=1;
        for(int k=0;k<count;k++){
            if(token>=(int)p->count||p->tokens[token].type!=J_NUMBER||!(p->tokens[token].number>=-1000000&&p->tokens[token].number<=1000000))return 0;
            values[k]=p->tokens[token].number;token=p->tokens[token].next;
        }
        for(int i=0;i<NR_WIDGETS;i++)if(s->widgets[i].used&&s->widgets[i].id==v->bindingId){
            memcpy(s->widgets[i].data,values,(size_t)count*sizeof(double));s->widgets[i].dataCount=count;return 1;
        }return 0;
    }
    if(t->kind!=2)return 0;
    if(v->bindingFamily==3){
        for(int i=0;i<NR_WIDGETS;i++){Widget*w=&s->widgets[i];if(w->used&&w->id==v->bindingId){
            int count=glyphString(&t->data,w->text,NR_MAX_TEXT);if(count<0)return 0;w->count=count;return 1;
        }}
    }
    if(v->bindingFamily==5){
        int index=nrFindWindow(s,v->bindingId);if(index<0)return 0;Window*w=&s->windows[index];
        int title=!strcmp(v->field,"title");int count=glyphString(&t->data,title?w->title:w->text,title?160:NR_MAX_TEXT);
        if(count<0)return 0;if(title)w->titleCount=count;else w->textCount=count;s->selectedWindow=w->id;return 1;
    }
    if(v->bindingFamily==6){
        for(int i=0;i<NR_TEXTS;i++){TextRun*q=&s->text[i];if(q->used&&q->id==v->bindingId){
            TextRun old=*q;int count=glyphString(&t->data,q->text,NR_MAX_TEXT);if(count<0)return 0;
            if(count>0&&(uint64_t)s->nextGlyphIdentity+count>=0xffffffffu)return 0;
            q->count=count;nrPrepareTextWithModels(q,s->textAlphabetTail[i],(int)s->textPhaseModel[i],&old,s->textAlphabetTail[i],(int)s->textPhaseModel[i],s->timeUs,&s->nextGlyphIdentity);q->startUs=s->timeUs;return 1;
        }}
    }
    if(v->bindingFamily==11){
        for(int i=0;i<NR_INDICATORS;i++)if(s->indicators[i].used&&s->indicators[i].id==v->bindingId){
            uint32_t glyphs[128];int count=glyphString(&t->data,glyphs,128);if(count<=0)return 0;
            for(int k=0;k<count;k++)if(glyphs[k]<32&&glyphs[k]!=10&&glyphs[k]!=9)return 0;
            memcpy(s->indicators[i].glyphs,glyphs,(size_t)count*sizeof(uint32_t));s->indicators[i].count=count;return 1;
        }return 0;
    }
    if(v->bindingFamily==10){
        int index=nrFindNode(s,v->bindingId);if(index<0)return 0;Node*n=&s->nodes[index];
        if(!strcmp(v->field,"label")||!strcmp(v->field,"detail")){
            int label=!strcmp(v->field,"label");int count=glyphString(&t->data,label?n->label:n->detail,label?256:512);
            if(count<0)return 0;if(label)n->labelCount=count;else n->detailCount=count;return 1;
        }
        const JToken*root=&t->data.tokens[0];char*out;int cap;
        if(!strcmp(v->field,"kind")){out=n->kind;cap=sizeof(n->kind);}
        else if(!strcmp(v->field,"status")){out=n->status;cap=sizeof(n->status);}
        else{out=n->sha;cap=sizeof(n->sha);}
        return nrStringSpan(t->data.json,root->start,root->end,out,cap)>=0;
    }
    return 0;
}
static int rootMatches(int kind,const IntentPayload*p){
    if(!p->count)return 0;int type=p->tokens[0].type;
    return kind==3||(kind==1&&(type==J_TRUE||type==J_FALSE))||(kind==2&&type==J_STRING);
}
int nrTypedAssign(State*s,int slot,const IntentPayload*p){
    TypedValue*t=&s->typedValues[slot];
    if(!rootMatches(t->kind,p))return 0;
    TypedValue candidate;memset(&candidate,0,sizeof(candidate));candidate.kind=t->kind;memcpy(&candidate.data,p,sizeof(*p));
    if(!nrTypedApply(s,&s->values[slot],&candidate))return 0;
    memcpy(t,&candidate,sizeof(candidate));return 1;
}
int nrTypedSet(State*s,int slot,const Json*j,int token){
    IntentPayload payload;if(!nrPayloadFromJson(j,token,&payload))return 0;return nrTypedAssign(s,slot,&payload);
}
int nrTypedExpression(NrContext*c,State*s,int slot,const Json*j,int token,int intentAt){
    const Intent*intent=0;
    if(intentAt>=0){double id;if(!nrNumber(j,intentAt,&id)||id<1||id>9007199254740991.0||id!=(uint64_t)id)return 0;
        for(int i=0;i<NR_INTENTS;i++)if(s->intents[i].used&&s->intents[i].id==(uint64_t)id)intent=&s->intents[i];
        if(!intent)return 0;
    }
    if(!nrCompileDataFormula(s,j,token,&c->dataFormulaScratch))return 0;
    double before[NR_VALUES];for(int i=0;i<NR_VALUES;i++)before[i]=s->values[i].value;
    IntentPayload result;
    if(!nrEvalDataFormula(c,s,&c->dataFormulaScratch,before,s->typedValues,intent,&result))return 0;
    return nrTypedAssign(s,slot,&result);
}
