#include "../src/internal.h"
#include <assert.h>
#include <stdlib.h>
static uint32_t read32(const unsigned char*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static int registrySave(NrContext*c,uint8_t*out,uint32_t bytes){
 assert(bytes==nrSnapshotSizeFor(c));int result=nrSave(c,out,bytes);
 if(!result){assert(bytes>=24&&!memcmp(out,"NRRC4SRC",8));assert(read32(out+16)==bytes-24);assert(read32(out+20)==nrCrc(out+24,bytes-24));}
 return result;
}
static int registryChecks(NrContext*context,uint8_t*saved,uint8_t*after,uint32_t snapshotSize){
    NrCharacterCellInfo inspected,sentinel;memset(&sentinel,42,sizeof(sentinel));inspected=sentinel;
    if(nrInspectCharacterCell(context,0,0,&inspected,sizeof(inspected))!=-2||memcmp(&inspected,&sentinel,sizeof(inspected)))return 14;
    const char*add="{\"op\":\"character-rule\",\"rule\":{\"id\":\"invert\",\"compositeSpace\":\"srgb\",\"foregroundEffects\":[{\"type\":\"invert\"}]}}";
    if(nrCommand(context,add,(uint32_t)strlen(add))||context->characterRuleCount!=1)return 2;
    if(registrySave(context,saved,snapshotSize))return 3;
    context->cells[0]=(NrCell){.glyph='A',.foreground=0xffffff,.background=0,.id=123};
    context->characterIndices[0]=UINT32_MAX;context->characterOwners[0]=0;
    nrDrawCharacterRules(context);
    if(context->cells[0].foreground||context->cells[0].glyph!='A'||context->cells[0].id!=123)return 4;
    if(registrySave(context,after,snapshotSize)||memcmp(saved,after,snapshotSize))return 5;
    const char*replace="{\"op\":\"character-rule\",\"rule\":{\"id\":\"invert\",\"enabled\":false}}";
    if(nrCommand(context,replace,(uint32_t)strlen(replace))||context->characterRuleCount!=1||context->characterRuleCache[0].style.enabled)return 6;
    if(nrLoad(context,saved,snapshotSize)||context->characterRuleCount!=1||!context->characterRuleCache[0].style.enabled)return 7;
    if(!nrRender(context)||registrySave(context,after,snapshotSize)||memcmp(saved,after,snapshotSize))return 8;
    if(nrInspectCharacterCell(context,0,0,&inspected,sizeof(inspected)))return 15;
    if(inspected.cell.glyph!=context->cells[0].glyph||inspected.cell.id!=context->cells[0].id)return 16;
    inspected=sentinel;
    if(nrInspectCharacterCell(context,-1,0,&inspected,sizeof(inspected))!=-1||memcmp(&inspected,&sentinel,sizeof(inspected)))return 17;
    const char*remove="{\"op\":\"remove-character-rule\",\"id\":\"invert\"}";
    if(nrCommand(context,remove,(uint32_t)strlen(remove))||context->characterRuleCount)return 9;
    if(nrInspectCharacterCell(context,0,0,&inspected,sizeof(inspected))!=-2||memcmp(&inspected,&sentinel,sizeof(inspected)))return 18;
    if(nrCommand(context,remove,(uint32_t)strlen(remove)))return 10;
    if(registrySave(context,saved,snapshotSize))return 11;
    const char*invalid="{\"op\":\"character-rule\",\"rule\":{\"id\":\"bad\",\"foregroundEffects\":[{\"type\":\"gamma\",\"value\":0}]}}";
    if(nrCommand(context,invalid,(uint32_t)strlen(invalid))!=-1||context->characterRuleCount)return 12;
    if(registrySave(context,after,snapshotSize)||memcmp(saved,after,snapshotSize))return 13;
    const char*ordered="{\"op\":\"batch\",\"commands\":[{\"op\":\"character-rule\",\"rule\":{\"id\":\"z\",\"priority\":0}},{\"op\":\"character-rule\",\"rule\":{\"id\":\"a\",\"priority\":0}},{\"op\":\"character-rule\",\"rule\":{\"id\":\"first\",\"priority\":-1}}]}";
    if(nrCommand(context,ordered,(uint32_t)strlen(ordered))||context->characterRuleCount!=3)return 19;
    if(strcmp(context->characterRuleCache[context->characterRuleOrder[0]].id,"first")||
       strcmp(context->characterRuleCache[context->characterRuleOrder[1]].id,"a")||
       strcmp(context->characterRuleCache[context->characterRuleOrder[2]].id,"z"))return 20;
    if(registrySave(context,saved,snapshotSize))return 21;
    int order[128];memcpy(order,context->characterRuleOrder,sizeof(order));
    if(!nrRender(context)||memcmp(order,context->characterRuleOrder,sizeof(order)))return 22;
    const char*reorder="{\"op\":\"character-rule\",\"rule\":{\"id\":\"z\",\"priority\":-2}}";
    if(nrCommand(context,reorder,(uint32_t)strlen(reorder))||strcmp(context->characterRuleCache[context->characterRuleOrder[0]].id,"z"))return 23;
    if(nrLoad(context,saved,snapshotSize)||
       strcmp(context->characterRuleCache[context->characterRuleOrder[0]].id,"first")||
       strcmp(context->characterRuleCache[context->characterRuleOrder[1]].id,"a")||
       strcmp(context->characterRuleCache[context->characterRuleOrder[2]].id,"z"))return 24;
    return 0;
}

int nrTestCharacterRegistry(void){
 static NrContext context;if(nrInit(&context,sizeof(context),42))return 1;
 /* Exercise a variable prompt payload while retaining every registry case. */
 const char*draft="{\"op\":\"draft\",\"text\":\"Registry snapshot source\",\"emitWeather\":false}";
 assert(nrCommand(&context,draft,(uint32_t)strlen(draft))==0);
 uint32_t size=nrSnapshotSizeFor(&context);assert(size>nrSnapshotSize());
 uint8_t*saved=malloc(size),*after=malloc(size);assert(saved&&after);
 int result=registryChecks(&context,saved,after,size);free(after);free(saved);return result;
}
