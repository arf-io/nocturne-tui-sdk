#include "internal.h"
static int fail(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int sourceRegion(NrContext*c,const CharacterRuleSource*source,CharacterRegion*out){
    return source->used==1&&source->length>0&&source->length<=4095&&source->json[source->length]==0&&
        nrParse(&c->characterJson,source->json,source->length)&&nrCompileCharacterRegion(&c->characterJson,0,out);
}
int nrCharacterRegionCommand(NrContext*c,State*s,const Json*j){
    int remove=nrEqual(j,nrField(j,0,"op"),"remove-character-region");
    if(!nrAllowed(j,0,remove?"op id":"op region"))return fail(c,"Unknown character region command field");
    char id[129];int region=nrField(j,0,"region");
    if(remove){if(nrString(j,nrField(j,0,"id"),id,sizeof(id))<1)return fail(c,"Character region ID required");}
    else{if(!nrCompileCharacterRegion(j,region,&c->characterRegionScratch))return fail(c,"Invalid character region");memcpy(id,c->characterRegionScratch.id,sizeof(id));}
    int slot=-1,freeSlot=-1;
    for(int i=0;i<1024;i++){
        if(!s->characterRegions[i].used){if(freeSlot<0)freeSlot=i;continue;}
        if(!sourceRegion(c,&s->characterRegions[i],&c->characterRegionScratch))return fail(c,"Invalid retained character region");
        if(!strcmp(id,c->characterRegionScratch.id))slot=i;
    }
    if(remove){if(slot>=0)memset(&s->characterRegions[slot],0,sizeof(s->characterRegions[slot]));return 0;}
    if(slot<0)slot=freeSlot;if(slot<0)return fail(c,"Character region capacity reached");
    int length=j->tokens[region].end-j->tokens[region].start;if(length<1||length>4095)return fail(c,"Character region source exceeds 4095 bytes");
    CharacterRuleSource*source=&s->characterRegions[slot];memset(source,0,sizeof(*source));source->used=1;source->length=length;
    memcpy(source->json,j->text+j->tokens[region].start,(size_t)length);return 0;
}
int nrValidateCharacterRegions(NrContext*c,const State*s){
    char ids[1024][129];int count=0;
    for(int i=0;i<1024;i++){
        const CharacterRuleSource*source=&s->characterRegions[i];
        if(!source->used){const uint8_t*bytes=(const uint8_t*)source;for(size_t k=0;k<sizeof(*source);k++)if(bytes[k])return 0;continue;}
        if(!sourceRegion(c,source,&c->characterRegionScratch))return 0;
        for(int k=0;k<count;k++)if(!strcmp(ids[k],c->characterRegionScratch.id))return 0;
        memcpy(ids[count++],c->characterRegionScratch.id,129);
        for(int k=source->length+1;k<4096;k++)if(source->json[k])return 0;
    }return 1;
}
void nrCacheCharacterRegions(NrContext*c){
    c->characterRegionCount=0;
    for(int i=0;i<1024;i++)if(c->state.characterRegions[i].used){
        if(!sourceRegion(c,&c->state.characterRegions[i],&c->characterRegionCache[c->characterRegionCount]))return;
        c->characterRegionCount++;
    }
}
