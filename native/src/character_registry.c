#include "internal.h"
static int fail(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int sourceRule(NrContext*c,const State*s,const CharacterRuleSource*source,CharacterRule*out){
    return source->used==1&&source->length>0&&source->length<=4095&&source->json[source->length]==0&&
        nrParse(&c->characterJson,source->json,source->length)&&nrCompileCharacterRule(s,&c->characterJson,0,out);
}
int nrCharacterRuleCommand(NrContext*c,State*s,const Json*j){
    int remove=nrEqual(j,nrField(j,0,"op"),"remove-character-rule");
    if(!nrAllowed(j,0,remove?"op id":"op rule"))return fail(c,"Unknown character rule command field");
    char id[129];int rule=nrField(j,0,"rule");
    if(remove){if(nrString(j,nrField(j,0,"id"),id,sizeof(id))<1)return fail(c,"Character rule ID required");}
    else{
        if(!nrCompileCharacterRule(s,j,rule,&c->characterRuleScratch))return fail(c,"Invalid character rule");
        memcpy(id,c->characterRuleScratch.id,sizeof(id));
    }
    int slot=-1,freeSlot=-1;
    for(int i=0;i<128;i++){
        if(!s->characterRules[i].used){if(freeSlot<0)freeSlot=i;continue;}
        if(!sourceRule(c,s,&s->characterRules[i],&c->characterRuleScratch))return fail(c,"Invalid retained character rule");
        if(!strcmp(id,c->characterRuleScratch.id))slot=i;
    }
    if(remove){if(slot>=0)memset(&s->characterRules[slot],0,sizeof(s->characterRules[slot]));return 0;}
    if(slot<0)slot=freeSlot;if(slot<0)return fail(c,"Character rule capacity reached");
    int length=j->tokens[rule].end-j->tokens[rule].start;
    if(length<1||length>4095)return fail(c,"Character rule source exceeds 4095 bytes");
    CharacterRuleSource*source=&s->characterRules[slot];memset(source,0,sizeof(*source));
    source->used=1;source->length=length;memcpy(source->json,j->text+j->tokens[rule].start,(size_t)length);return 0;
}
int nrValidateCharacterRules(NrContext*c,const State*s){
    char ids[128][129];int count=0;
    for(int i=0;i<128;i++){
        const CharacterRuleSource*source=&s->characterRules[i];
        if(!source->used){const uint8_t*bytes=(const uint8_t*)source;for(size_t k=0;k<sizeof(*source);k++)if(bytes[k])return 0;continue;}
        if(!sourceRule(c,s,source,&c->characterRuleScratch))return 0;
        for(int k=0;k<count;k++)if(!strcmp(ids[k],c->characterRuleScratch.id))return 0;
        memcpy(ids[count++],c->characterRuleScratch.id,129);
        for(int k=source->length+1;k<4096;k++)if(source->json[k])return 0;
    }return 1;
}
void nrCacheCharacterRules(NrContext*c){
    c->characterRuleCount=0;
    for(int i=0;i<128;i++)if(c->state.characterRules[i].used){
        if(!sourceRule(c,&c->state,&c->state.characterRules[i],&c->characterRuleCache[c->characterRuleCount]))return;
        c->characterRuleCount++;
    }
    /* Retained source determines order. Resolve it once on commit/restore;
     * rendering only evaluates compiled rules against the completed cells. */
    for(int i=0;i<c->characterRuleCount;i++){
        int at=i;
        while(at>0&&nrCharacterRuleCompare(&c->characterRuleCache[i],&c->characterRuleCache[c->characterRuleOrder[at-1]])<0){
            c->characterRuleOrder[at]=c->characterRuleOrder[at-1];at--;
        }
        c->characterRuleOrder[at]=i;
    }
}
void nrDrawCharacterRules(NrContext*c){
    if(!c->characterRuleCount)return;
    const State*s=nrView(c);
    for(uint32_t y=0;y<s->height;y++)for(uint32_t x=0;x<s->width;x++)for(int i=0;i<c->characterRuleCount;i++){
        NrCell result;if(nrApplyCharacterRuleCell(c,&c->characterRuleCache[c->characterRuleOrder[i]],(int)x,(int)y,&result)>0)c->cells[(size_t)y*s->width+x]=result;
    }
}
