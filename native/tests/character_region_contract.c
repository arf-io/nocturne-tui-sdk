#include "character_test_context.h"
static int characterRegionChecks(CharacterTestContext*fixture){
    NrContext*context=fixture->context;static Json json;

    const char*source="{\"id\":\"region\",\"path\":\"/app/custom\",\"role\":\"user-text\",\"state\":\"selected\",\"cells\":[0,2,4294967295],\"indices\":[7,9,10]}";
    if(!nrParse(&json,source,(int)strlen(source))||!nrCompileCharacterRegion(&json,0,&context->characterRegionCache[0]))return 2;
    context->characterRegionCount=1;characterTestRemember(fixture);
    context->cells[0]=(NrCell){.glyph='A',.id=123};nrDrawCharacterRegions(context);
    if(context->characterIndices[0]!=7||context->characterIndices[2]!=9||context->cells[0].id!=123||context->cells[0].glyph!='A')return 3;
    const char*role,*state,*path;nrCharacterCellOwner(context,0,&role,&state,&path);
    if(strcmp(role,"user-text")||strcmp(state,"selected")||strcmp(path,"/app/custom"))return 4;
    source="{\"id\":\"overlap\",\"path\":\"/app/overlay\",\"rect\":{\"x\":-1,\"y\":0,\"width\":3,\"height\":1}}";
    if(!nrParse(&json,source,(int)strlen(source))||!nrCompileCharacterRegion(&json,0,&context->characterRegionCache[1]))return 5;
    context->characterRegionCount=2;nrDrawCharacterRegions(context);
    if(context->characterIndices[0]!=0||context->characterIndices[1]!=1||context->characterIndices[2]!=9)return 6;
    nrCharacterCellOwner(context,0,&role,&state,&path);if(strcmp(path,"/app/overlay"))return 7;
    if(!characterTestUnchanged(fixture))return 8;
    const char*invalid[]={"{\"id\":\"x\",\"path\":\"relative\"}","{\"id\":\"x\",\"path\":\"/x\",\"indices\":[1]}","{\"id\":\"x\",\"path\":\"/x\",\"cells\":[1,2],\"indices\":[1]}","{\"id\":\"x\",\"path\":\"/x\",\"cells\":[-1]}"};
    static CharacterRegion previous;context->characterRegionScratch=context->characterRegionCache[0];previous=context->characterRegionScratch;
    for(unsigned i=0;i<4;i++){
        if(!nrParse(&json,invalid[i],(int)strlen(invalid[i]))||nrCompileCharacterRegion(&json,0,&context->characterRegionScratch))return 9;
        if(memcmp(&previous,&context->characterRegionScratch,sizeof(previous)))return 10;
    }
    if(nrCompileCharacterRegion(NULL,0,&context->characterRegionScratch)||memcmp(&previous,&context->characterRegionScratch,sizeof(previous)))return 11;
    if(nrCompileCharacterRegion(&json,0,NULL))return 12;
    return 0;
}

int nrTestCharacterRegion(void){return characterTestRun(characterRegionChecks);}
