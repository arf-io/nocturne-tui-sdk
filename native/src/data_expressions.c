#include "internal.h"
/* Compiled typed expressions own bounded source literals, resolved value slots,
 * and validated pointers. Runtime evaluation never parses or allocates. */
static int compile(const State*,const Json*,int,int,int,DataFormula*);
static int numericChildren(const State*s,const Json*j,int at,int root,int depth,int index,DataFormula*f){
    const char*names[]={"add","subtract","multiply","divide","min","max","negate","abs","clamp","floor","ceil","round","lerp","remap","convert"};
    int op=-1;for(int k=0;k<15;k++)if(nrField(j,at,names[k])>=0){op=k;break;}
    if(op<0||!nrAllowed(j,at,names[op]))return -1;
    NumericFormulaNode*n=&f->tree.nodes[index];n->kind=103+op;n->ref=-1;
    int arg=nrField(j,at,names[op]),children[16],count=0;
    if(op==6||op==7||(op>=9&&op<=11))children[count++]=arg;
    else if(op==8||op==12||op==13||op==14){
        const char*clamp[]={"value","min","max"},*lerp[]={"from","to","amount"},*remap[]={"value","inMin","inMax","outMin","outMax"};
        if(j->tokens[arg].type!=J_OBJECT)return -1;
        if(op==14){
            if(!nrAllowed(j,arg,"value from to")||(n->ref=nrFormulaUnitRef(j,nrField(j,arg,"from"),nrField(j,arg,"to")))<0)return -1;
            children[count++]=nrField(j,arg,"value");
        }else{
            if(!nrAllowed(j,arg,op==8?"value min max":op==12?"from to amount":"value inMin inMax outMin outMax"))return -1;
            count=op==13?5:3;for(int k=0;k<count;k++)children[k]=nrField(j,arg,op==8?clamp[k]:op==12?lerp[k]:remap[k]);
        }
    }else{
        if(j->tokens[arg].type!=J_ARRAY)return -1;count=j->tokens[arg].count;
        if(count<2||count>16||((op==1||op==3)&&count!=2))return -1;
        int child=arg+1;for(int k=0;k<count;k++){children[k]=child;child=j->tokens[child].next;}
    }
    n->childCount=count;
    for(int k=0;k<count;k++){int child=compile(s,j,children[k],root,depth+1,f);if(child<0)return -1;n->children[k]=(uint8_t)child;}
    return index;
}
static int compile(const State*s,const Json*j,int at,int root,int depth,DataFormula*f){
    if(at<0||at>=j->count||depth>8||f->tree.count>=31)return -1;
    int index=f->tree.count++;NumericFormulaNode*n=&f->tree.nodes[index];n->ref=-1;
    int type=j->tokens[at].type;
    if(type!=J_OBJECT){if(type==J_ARRAY)return -1;n->ref=at-root;return index;}
    int arg=nrField(j,at,"literal");
    if(arg>=0){if(!nrAllowed(j,at,"literal"))return -1;n->ref=arg-root;return index;}
    arg=nrField(j,at,"path");
    if(arg>=0){char path[128];if(!nrAllowed(j,at,"path pointer")||nrString(j,arg,path,sizeof(path))<0)return -1;n->kind=1;
        for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&!strcmp(s->values[i].path,path))n->ref=i;
        int pointer=nrField(j,at,"pointer");
        if(pointer>=0){
            if(n->ref<0||!s->typedValues[n->ref].kind||nrString(j,pointer,f->tree.intentPaths[index],128)<0||!nrPayloadPathValid(f->tree.intentPaths[index]))return -1;
            n->kind=11;
        }
        return n->ref>=0?index:-1;
    }
    arg=nrField(j,at,"intentPath");
    if(arg>=0){if(!nrAllowed(j,at,"intentPath")||nrString(j,arg,f->tree.intentPaths[index],128)<0||!nrPayloadPathValid(f->tree.intentPaths[index]))return -1;
        n->kind=2;f->tree.usesIntent=1;return index;
    }
    const char*names[]={"concat","and","or","not","equal","if","array","object","lessThan","lessOrEqual","greaterThan","greaterOrEqual"};int op=-1;
    for(int k=0;k<12;k++)if(nrField(j,at,names[k])>=0){op=k;break;}
    if(op<0){
        NumericFormula numeric;if(!nrCompileTriggerFormula(s,j,at,&numeric))return numericChildren(s,j,at,root,depth,index,f);
        if(index+numeric.count>31)return -1;
        for(int k=0;k<numeric.count;k++){
            NumericFormulaNode copy=numeric.nodes[k];copy.kind+=100;
            for(int child=0;child<copy.childCount;child++)copy.children[child]+=(uint8_t)index;
            f->tree.nodes[index+k]=copy;memcpy(f->tree.intentPaths[index+k],numeric.intentPaths[k],128);
        }
        f->tree.count=index+numeric.count;f->tree.usesIntent|=numeric.usesIntent;return index;
    }
    if(!nrAllowed(j,at,names[op]))return -1;n->kind=op>=8?op+4:op+3;arg=nrField(j,at,names[op]);
    int children[16],count=0;
    if(op==7){
        if(j->tokens[arg].type!=J_OBJECT||j->tokens[arg].count>16)return -1;
        n->ref=arg-root;count=j->tokens[arg].count;int key=arg+1;
        for(int k=0;k<count;k++){children[k]=key+1;key=j->tokens[key+1].next;}
    }
    else if(op==3){children[count++]=arg;}
    else if(op==5){if(j->tokens[arg].type!=J_OBJECT||!nrAllowed(j,arg,"condition then else"))return -1;
        children[count++]=nrField(j,arg,"condition");children[count++]=nrField(j,arg,"then");children[count++]=nrField(j,arg,"else");}
    else{if(j->tokens[arg].type!=J_ARRAY)return -1;count=j->tokens[arg].count;
        if(count<(op==6?0:2)||count>16||((op==4||op>=8)&&count!=2))return -1;
        int child=arg+1;for(int k=0;k<count;k++){children[k]=child;child=j->tokens[child].next;}
    }
    n->childCount=count;
    for(int k=0;k<count;k++){int child=compile(s,j,children[k],root,depth+1,f);if(child<0)return -1;n->children[k]=(uint8_t)child;}
    return index;
}
int nrCompileDataFormula(const State*s,const Json*j,int at,DataFormula*f){
    memset(f,0,sizeof(*f));
    if(!nrPayloadFromJson(j,at,&f->source))return 0;
    return compile(s,j,at,at,1,f)==0;
}
typedef struct {int type,token;double number;const IntentPayload*source;} Result;
static int tokenResult(const IntentPayload*p,int at,Result*out){
    if(!p||at<0||at>=(int)p->count)return 0;
    *out=(Result){p->tokens[at].type,at,p->tokens[at].number,p};return 1;
}
static int stringEqual(const IntentPayload*a,int ai,const IntentPayload*b,int bi){
    uint32_t left[4096],right[4096];const JToken*x=&a->tokens[ai],*y=&b->tokens[bi];
    int n=nrDecodeSpan(a->json,x->start,x->end,left,4096),m=nrDecodeSpan(b->json,y->start,y->end,right,4096);
    return n>=0&&n==m&&!memcmp(left,right,(size_t)n*sizeof(uint32_t));
}
static int equal(Result a,Result b,int depth){
    if(depth>8||a.type!=b.type)return 0;
    if(a.type==J_NUMBER)return a.number==b.number;
    if(a.type==J_TRUE||a.type==J_FALSE||a.type==J_NULL)return 1;
    if(!a.source||!b.source)return 0;
    if(a.type==J_STRING)return stringEqual(a.source,a.token,b.source,b.token);
    const JToken*x=&a.source->tokens[a.token],*y=&b.source->tokens[b.token];
    if(x->count!=y->count)return 0;
    int left=a.token+1,right=b.token+1;
    if(a.type==J_ARRAY){
        for(int k=0;k<x->count;k++){
            Result l,r;if(!tokenResult(a.source,left,&l)||!tokenResult(b.source,right,&r)||!equal(l,r,depth+1))return 0;
            left=a.source->tokens[left].next;right=b.source->tokens[right].next;
        }return 1;
    }
    if(a.type!=J_OBJECT)return 0;
    for(int k=0;k<x->count;k++){
        int key=-1;right=b.token+1;
        for(int n=0;n<y->count;n++){
            if(stringEqual(a.source,left,b.source,right)){key=right;break;}
            right=b.source->tokens[right+1].next;
        }
        Result l,r;if(key<0||!tokenResult(a.source,left+1,&l)||!tokenResult(b.source,key+1,&r)||!equal(l,r,depth+1))return 0;
        left=a.source->tokens[left+1].next;
    }return 1;
}
static int appendText(IntentPayload*p,const char*text,int length){
    if(length<0||p->length+(uint32_t)length>4095)return 0;
    memcpy(p->json+p->length,text,(size_t)length);p->length+=(uint32_t)length;return 1;
}
static int appendResult(IntentPayload*p,Result value){
    int base=(int)p->count,offset=(int)p->length;
    if(value.source){
        const IntentPayload*source=value.source;const JToken*root=&source->tokens[value.token];
        int count=root->next-value.token;if(count<1||base+count>128)return 0;
        if(!appendText(p,source->json+root->start,root->end-root->start))return 0;
        for(int k=0;k<count;k++){
            const JToken*t=&source->tokens[value.token+k];JToken*out=&p->tokens[base+k];
            out->type=t->type;out->start=offset+t->start-root->start;out->end=offset+t->end-root->start;
            out->next=base+t->next-value.token;out->count=t->count;out->number=t->number;
        }
        p->count+=(uint32_t)count;return 1;
    }
    if(base>=128)return 0;
    if(value.type==J_NUMBER){
        char text[1200];int length=nrJsonNumber(value.number,text,sizeof(text));
        if(length<0||!appendText(p,text,length))return 0;
        p->tokens[base]=(JToken){.type=J_NUMBER,.start=offset,.end=(int)p->length,.next=base+1,.number=value.number};p->count++;return 1;
    }
    if(value.type!=J_TRUE&&value.type!=J_FALSE&&value.type!=J_NULL)return 0;
    const char*text=value.type==J_TRUE?"true":value.type==J_FALSE?"false":"null";
    if(!appendText(p,text,(int)strlen(text)))return 0;
    p->tokens[base]=(JToken){.type=value.type,.start=offset,.end=(int)p->length,.next=base+1};p->count++;return 1;
}
static int resultDepth(const IntentPayload*p,int at,int depth){
    if(depth>8||at<0||at>=(int)p->count)return 0;
    const JToken*t=&p->tokens[at];
    if(t->type==J_ARRAY||t->type==J_OBJECT){
        for(int child=at+1;child<t->next;child=p->tokens[child].next)if(!resultDepth(p,child,depth+1))return 0;
    }
    return 1;
}
static int truth(Result value,int*out){if(value.type!=J_TRUE&&value.type!=J_FALSE)return 0;*out=value.type==J_TRUE;return 1;}
static int evaluate(NrContext*c,const State*s,const DataFormula*f,int at,const double*before,const TypedValue*typed,const Intent*intent,Result*out){
    if(at<0||at>=f->tree.count)return 0;
    const NumericFormulaNode*n=&f->tree.nodes[at];
    if(n->kind==0)return tokenResult(&f->source,n->ref,out);
    if(n->kind==1){
        if(n->ref<0||n->ref>=NR_VALUES||!s->values[n->ref].used)return 0;
        if(typed[n->ref].kind)return tokenResult(&typed[n->ref].data,0,out);
        *out=(Result){J_NUMBER,0,before[n->ref],0};return 1;
    }
    if(n->kind==11){
        int selected;if(n->ref<0||n->ref>=NR_VALUES||!typed[n->ref].kind)return 0;
        const IntentPayload*p=&typed[n->ref].data;
        return nrPayloadResolve(p,f->tree.intentPaths[at],&selected)&&tokenResult(p,selected,out);
    }
    if(n->kind==2){
        if(!intent)return 0;const IntentPayload*p=&s->intentPayloads[intent-s->intents];int selected;
        return nrPayloadResolve(p,f->tree.intentPaths[at],&selected)&&tokenResult(p,selected,out);
    }
    if(n->kind>=100&&n->kind<=102){
        double number=n->value;
        if(n->kind==101){if(n->ref<0||n->ref>=NR_VALUES||typed[n->ref].kind)return 0;number=before[n->ref];}
        if(n->kind==102){if(!intent)return 0;switch(n->ref){case 0:number=intent->value;break;case 1:number=(double)intent->id;break;case 2:number=intent->messageId;break;case 3:number=intent->actionId;break;case 4:number=(double)intent->messageSequence;break;case 5:number=(double)intent->atUs;break;default:return 0;}}
        if(!(number>=-1e12&&number<=1e12))return 0;*out=(Result){J_NUMBER,0,number,0};return 1;
    }
    if(n->kind==118){
        if(!intent)return 0;const IntentPayload*p=&s->intentPayloads[intent-s->intents];int selected;
        if(!nrPayloadResolve(p,f->tree.intentPaths[at],&selected)||!tokenResult(p,selected,out))return 0;
        return out->type==J_NUMBER&&out->number>=-1e12&&out->number<=1e12;
    }
    Result args[16];
    if(n->kind==8){int condition;
        if(!evaluate(c,s,f,n->children[0],before,typed,intent,&args[0])||!truth(args[0],&condition))return 0;
        return evaluate(c,s,f,n->children[condition?1:2],before,typed,intent,out);
    }
    for(int k=0;k<n->childCount;k++)if(!evaluate(c,s,f,n->children[k],before,typed,intent,&args[k]))return 0;
    if(n->kind==9||n->kind==10){
        IntentPayload*p=&c->dataScratch[at];memset(p,0,sizeof(*p));p->count=1;
        int object=n->kind==10,key=object?n->ref+1:0;
        if(!appendText(p,object?"{":"[",1))return 0;
        for(int k=0;k<n->childCount;k++){
            if(k&&!appendText(p,",",1))return 0;
            if(object){Result name;if(!tokenResult(&f->source,key,&name)||name.type!=J_STRING||!appendResult(p,name)||!appendText(p,":",1))return 0;
                key=f->source.tokens[key+1].next;
            }
            if(!appendResult(p,args[k]))return 0;
        }
        if(!appendText(p,object?"}":"]",1))return 0;
        p->tokens[0]=(JToken){.type=object?J_OBJECT:J_ARRAY,.end=(int)p->length,.next=(int)p->count,.count=n->childCount};
        if(!resultDepth(p,0,1))return 0;
        return tokenResult(p,0,out);
    }
    if(n->kind>=103&&n->kind<=117){
        double numbers[16],result;for(int k=0;k<n->childCount;k++){if(args[k].type!=J_NUMBER)return 0;numbers[k]=args[k].number;}
        if(!nrNumericOperation(n->kind-100,n->ref,numbers,n->childCount,&result))return 0;
        *out=(Result){J_NUMBER,0,result,0};return 1;
    }
    if(n->kind==3){
        IntentPayload*p=&c->dataScratch[at];memset(p,0,sizeof(*p));int length=1;p->json[0]='"';
        for(int k=0;k<n->childCount;k++){
            if(args[k].type!=J_STRING||!args[k].source)return 0;
            const JToken*t=&args[k].source->tokens[args[k].token];int span=t->end-t->start-2;
            if(span<0||length+span+1>4095)return 0;
            memcpy(p->json+length,args[k].source->json+t->start+1,(size_t)span);length+=span;
        }
        p->json[length++]='"';p->length=(uint32_t)length;p->count=1;
        p->tokens[0]=(JToken){.type=J_STRING,.start=0,.end=length,.next=1};return tokenResult(p,0,out);
    }
    int value=0;
    if(n->kind>=12&&n->kind<=15){
        if(args[0].type!=J_NUMBER||args[1].type!=J_NUMBER)return 0;
        double a=args[0].number,b=args[1].number;
        value=n->kind==12?a<b:n->kind==13?a<=b:n->kind==14?a>b:a>=b;
    }
    else if(n->kind==7)value=equal(args[0],args[1],1);
    else if(n->kind==6){if(!truth(args[0],&value))return 0;value=!value;}
    else if(n->kind==4||n->kind==5){value=n->kind==4;
        for(int k=0;k<n->childCount;k++){int next;if(!truth(args[k],&next))return 0;value=n->kind==4?(value&&next):(value||next);}
    }else return 0;
    *out=(Result){value?J_TRUE:J_FALSE,0,0,0};return 1;
}
int nrEvalDataNumber(NrContext*c,const State*s,const DataFormula*f,const double*before,const TypedValue*typed,const Intent*intent,double*out){
    Result result;
    if(f->tree.count<1||f->tree.count>31||!evaluate(c,s,f,0,before,typed,intent,&result)||result.type!=J_NUMBER||!(result.number>=-1e12&&result.number<=1e12))return 0;
    *out=result.number;return 1;
}
int nrDataNumericExpression(NrContext*c,const State*s,const Json*j,int at,int intentAt,double*out){
    const Intent*intent=0;
    if(intentAt>=0){double id;if(!nrNumber(j,intentAt,&id)||id<1||id>9007199254740991.0||id!=(uint64_t)id)return 0;
        for(int i=0;i<NR_INTENTS;i++)if(s->intents[i].used&&s->intents[i].id==(uint64_t)id)intent=&s->intents[i];
        if(!intent)return 0;
    }
    if(!nrCompileDataFormula(s,j,at,&c->dataFormulaScratch))return 0;
    double before[NR_VALUES];for(int i=0;i<NR_VALUES;i++)before[i]=s->values[i].value;
    return nrEvalDataNumber(c,s,&c->dataFormulaScratch,before,s->typedValues,intent,out);
}
int nrEvalDataFormula(NrContext*c,const State*s,const DataFormula*f,const double*before,const TypedValue*typed,const Intent*intent,IntentPayload*out){
    Result result;
    if(f->tree.count<1||f->tree.count>31||!evaluate(c,s,f,0,before,typed,intent,&result))return 0;
    if(result.source)return nrPayloadSlice(result.source,result.token,out);
    memset(out,0,sizeof(*out));return appendResult(out,result);
}
static int validate(NrContext*c,const State*s,const DataFormula*f,int used,int event){
    DataFormula*expected=&c->dataFormulaScratch;
    if(!f->tree.count){memset(expected,0,sizeof(*expected));return !memcmp(f,expected,sizeof(*f));}
    if(!used||s->schema<NR_STATE_SCHEMA_GENERAL_API||f->source.length<1||f->source.length>4095||f->source.json[f->source.length])return 0;
    char wrapped[4120];memcpy(wrapped,"{\"expression\":",14);memcpy(wrapped+14,f->source.json,f->source.length);wrapped[14+f->source.length]='}';
    if(!nrParse(&c->repeatJson,wrapped,(int)f->source.length+15))return 0;
    if(!nrCompileDataFormula(s,&c->repeatJson,nrField(&c->repeatJson,0,"expression"),expected)||memcmp(f,expected,sizeof(*f)))return 0;
    return !f->tree.usesIntent||event;
}
int nrValidateDataFormulas(NrContext*c,const State*s){
    for(int i=0;i<NR_TRIGGERS;i++){
        const Trigger*t=&s->triggers[i];
        if(!validate(c,s,&s->triggerDataFormulas[i],t->used,t->eventPath[0])||!validate(c,s,&s->triggerGuardFormulas[i],t->used,t->eventPath[0]))return 0;
        if(t->used){
            int data=s->triggerDataFormulas[i].tree.count>0,guard=s->triggerGuardFormulas[i].tree.count>0;
            if(s->typedValues[t->target].kind&&(!data||t->action))return 0;
            if(data&&s->triggerFormulas[i].count)return 0;
            if(guard&&(t->conditionCount!=1||t->conditions[0].kind!=5))return 0;
            for(int k=0;k<t->conditionCount;k++)if(t->conditions[k].kind==5&&!guard)return 0;
        }
    }
    for(int i=0;i<NR_STYLE_RULES;i++){
        const StyleRule*r=&s->styleRules[i];const DataFormula*f=&s->styleGuardFormulas[i];
        if(!validate(c,s,f,r->used,0))return 0;
        if(f->tree.count&&(r->guard.conditionCount!=1||r->guard.conditions[0].kind!=5))return 0;
    }
    return 1;
}
