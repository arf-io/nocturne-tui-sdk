#include "internal.h"
static int fail(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int payloadDepth(const Json*j,int at,int depth){
    if(at<0||at>=j->count||depth>8)return 0;
    const JToken*t=&j->tokens[at];
    if(t->type==J_ARRAY||t->type==J_OBJECT){
        for(int child=at+1;child<t->next;child=j->tokens[child].next)
            if(!payloadDepth(j,child,depth+1))return 0;
    }return 1;
}
static int payloadTokens(const Json*j,int at){
    if(at<0||at>=j->count||j->tokens[at].next-at>128||!payloadDepth(j,at,1))return 0;
    uint32_t glyphs[4096];
    for(int i=at;i<j->tokens[at].next;i++)if(j->tokens[i].type==J_STRING&&nrDecode(j,i,glyphs,4096)<0)return 0;
    return 1;
}
static JToken normalizedToken(const Json*j,int root,int at){
    const JToken*source=&j->tokens[at];JToken token;memset(&token,0,sizeof(token));
    token.type=source->type;token.start=source->start-j->tokens[root].start;token.end=source->end-j->tokens[root].start;
    token.next=source->next-root;token.count=source->count;token.number=source->number;return token;
}
int nrPayloadFromJson(const Json*j,int at,IntentPayload*out){
    if(at<0||at>=j->count)return 0;
    int length=j->tokens[at].end-j->tokens[at].start;
    if(length<=0||length>4095||!payloadTokens(j,at))return 0;
    memset(out,0,sizeof(*out));out->length=(uint32_t)length;out->count=(uint32_t)(j->tokens[at].next-at);
    memcpy(out->json,j->text+j->tokens[at].start,(size_t)length);
    for(uint32_t k=0;k<out->count;k++)out->tokens[k]=normalizedToken(j,at,at+(int)k);
    return 1;
}
int nrPayloadSlice(const IntentPayload*source,int at,IntentPayload*out){
    if(at<0||at>=(int)source->count)return 0;
    const JToken*root=&source->tokens[at];int length=root->end-root->start,count=root->next-at;
    if(length<1||length>4095||count<1||count>128||root->next>(int)source->count)return 0;
    memset(out,0,sizeof(*out));out->length=(uint32_t)length;out->count=(uint32_t)count;
    memcpy(out->json,source->json+root->start,(size_t)length);
    for(int k=0;k<count;k++){
        const JToken*t=&source->tokens[at+k];JToken*q=&out->tokens[k];
        q->type=t->type;q->start=t->start-root->start;q->end=t->end-root->start;q->next=t->next-at;q->count=t->count;q->number=t->number;
    }
    return 1;
}
int nrHostEventCommand(NrContext*c,State*s,const Json*j){
    if(!nrAllowed(j,0,"op event value payload"))return fail(c,"Unknown host event field");
    char event[128];int at=nrField(j,0,"event");
    if(at<0||nrString(j,at,event,sizeof(event))<0||!nrEventPath(event))return fail(c,"Host event path required");
    double value=0;at=nrField(j,0,"value");
    if(at>=0&&(!nrNumber(j,at,&value)||!(value>=-1000000&&value<=1000000)))return fail(c,"Host event numeric value bounds");
    int payload=nrField(j,0,"payload"),length=0;
    if(payload>=0){length=j->tokens[payload].end-j->tokens[payload].start;
        if(length<=0||length>4095||!payloadTokens(j,payload))return fail(c,"Host payload byte/node/depth/Unicode bounds");}
    int slot=-1;for(int i=0;i<NR_INTENTS;i++)if(!s->intents[i].used){slot=i;break;}
    if(slot<0||s->nextIntent>9007199254740991ull)return fail(c,"Intent capacity reached; acknowledge consumed intentions");
    Intent*q=&s->intents[slot];memset(q,0,sizeof(*q));
    q->used=1;q->id=s->nextIntent++;q->atUs=s->timeUs;q->value=value;memcpy(q->event,event,strlen(event)+1);
    IntentPayload*p=&s->intentPayloads[slot];memset(p,0,sizeof(*p));p->length=(uint32_t)length;
    if(length){memcpy(p->json,j->text+j->tokens[payload].start,(size_t)length);
        p->count=(uint32_t)(j->tokens[payload].next-payload);
        for(uint32_t k=0;k<p->count;k++)p->tokens[k]=normalizedToken(j,payload,payload+(int)k);
    }
    return nrEvaluateValues(c,s)?0:fail(c,"Host event trigger rejected; transaction rolled back");
}
static int storageValid(const IntentPayload*p){
    if(p->length>4095||p->json[p->length]||p->count>128||(!p->length&&p->count)||(p->length&&!p->count))return 0;
    JToken empty={0};
    for(uint32_t k=0;k<128;k++){
        const JToken*t=&p->tokens[k];
        if(k>=p->count){if(memcmp(t,&empty,sizeof(empty)))return 0;continue;}
        if(t->type<J_OBJECT||t->type>J_NULL||t->start<0||t->end<=t->start||t->end>(int)p->length||t->next<=(int)k||t->next>(int)p->count||t->count<0||t->count>128)return 0;
    }
    if(p->count&&(p->tokens[0].start||p->tokens[0].end!=(int)p->length||p->tokens[0].next!=(int)p->count))return 0;
    for(uint32_t k=p->length;k<4096;k++)if(p->json[k])return 0;
    return 1;
}
int nrTypedStorageValid(const State*s){
    TypedValue zero={0};
    for(int i=0;i<NR_VALUES;i++){
        const TypedValue*t=&s->typedValues[i];const Value*v=&s->values[i];
        if(!t->kind){if(memcmp(t,&zero,sizeof(*t)))return 0;continue;}
        if(!v->used||s->schema<NR_STATE_SCHEMA_GENERAL_API||t->kind<1||t->kind>3||t->padding||v->value!=0||!storageValid(&t->data)||!t->data.count)return 0;
        int type=t->data.tokens[0].type;
        if(!nrTypedBindingValid(v,t->kind))return 0;
        if((t->kind==1&&type!=J_TRUE&&type!=J_FALSE)||(t->kind==2&&type!=J_STRING)||(t->kind==3&&v->bindingFamily&&!nrWidgetDataPayloadValid(&t->data)))return 0;
    }
    return 1;
}
int nrIntentPayloadStorageValid(const State*s){
    for(int i=0;i<NR_INTENTS;i++){
        const IntentPayload*p=&s->intentPayloads[i];const Intent*q=&s->intents[i];
        if(!storageValid(p)||(p->length&&(!q->used||q->messageId||s->schema<NR_STATE_SCHEMA_GENERAL_API)))return 0;
    }
    return nrTypedStorageValid(s);
}
static int validatePayload(NrContext*c,const IntentPayload*p){
    if(!p->length)return 1;
    char wrapped[4120];memcpy(wrapped,"{\"payload\":",11);
    memcpy(wrapped+11,p->json,p->length);wrapped[11+p->length]='}';
    if(!nrParse(&c->repeatJson,wrapped,(int)p->length+12))return 0;
    int root=nrField(&c->repeatJson,0,"payload");
    if(!payloadTokens(&c->repeatJson,root)||(uint32_t)(c->repeatJson.tokens[root].next-root)!=p->count)return 0;
    for(uint32_t k=0;k<p->count;k++){JToken token=normalizedToken(&c->repeatJson,root,root+(int)k);if(memcmp(&token,&p->tokens[k],sizeof(token)))return 0;}
    return 1;
}
int nrValidateIntentPayloads(NrContext*c,const State*s){
    if(!nrIntentPayloadStorageValid(s))return 0;
    for(int i=0;i<NR_INTENTS;i++)if(!validatePayload(c,&s->intentPayloads[i]))return 0;
    for(int i=0;i<NR_VALUES;i++)if(!validatePayload(c,&s->typedValues[i].data))return 0;
    return nrValidateDataFormulas(c,s);
}
