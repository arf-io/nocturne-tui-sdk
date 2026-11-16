#include "character_test_context.h"
/* Authored now; executed only with the complete general API gate. */
static int characterRenderChecks(CharacterTestContext*fixture){
    NrContext*context=fixture->context;


    characterTestRemember(fixture);
    context->clip=(ClipRect){0,0,(int)context->state.width,(int)context->state.height};
    uint32_t text[]={'A','\n',0x1f642,'\t','Z'};
    nrText(context,0,0,text,5,2,0xffffff,1,NR_ID_WIDGET|7);
    unsigned width=context->state.width;
    if(context->characterIndices[0]!=0||context->characterIndices[width]!=2||
       context->characterIndices[width+1]!=3||context->characterIndices[2*width]!=4)return 2;
    if(context->cells[width].glyph!=0x1f642||context->cells[width+1].glyph!=' '||
       context->cells[width].id!=(NR_ID_WIDGET|7))return 3;
    if(context->characterOwners[width]!=((1u<<16)|7))return 10;
    nrIndexedGlyph(context,0,1,'X',0xff0000,0,0,99);
    if(context->characterIndices[width]!=2||context->cells[width].glyph!=0x1f642)return 4;
    context->clip=(ClipRect){1,0,2,3};
    nrIndexedGlyph(context,0,1,'X',0xff0000,1,0,99);
    if(context->characterIndices[width]!=2)return 5;
    nrGlyph(context,1,1,'B',0xffffff,1,NR_ID_WINDOW|3);
    if(context->characterIndices[width+1]!=UINT32_MAX||context->cells[width+1].id!=(NR_ID_WINDOW|3))return 6;
    if(context->characterOwners[width+1]!=((2u<<16)|3))return 11;
    context->characterOwner=(4u<<16)|13;
    nrIndexedGlyph(context,1,1,'T',0xffffff,1,0,8);
    if(context->cells[width+1].id||context->characterOwners[width+1]!=((4u<<16)|13)||context->characterIndices[width+1]!=8)return 12;
    context->characterOwner=0;
    /* A clipped source prefix must not renumber its surviving characters. */
    uint32_t clipped[]={'a','b','c'};
    nrText(context,-1,2,clipped,3,3,0xffffff,1,NR_ID_WIDGET|9);
    if(context->characterIndices[2*width+1]!=2||context->cells[2*width+1].glyph!='c')return 7;
    nrText(context,INT32_MAX,1,clipped,3,3,0xffffff,1,0);
    nrText(context,INT32_MIN,INT32_MIN,text,5,2,0xffffff,1,0);
    nrText(context,0,INT32_MAX,text,5,2,0xffffff,1,0);
    if(context->characterIndices[2*width+1]!=2)return 9;
    if(!characterTestUnchanged(fixture))return 8;
    /* Disabled components have semantic ownership but no interactive ID. */
    if(characterTestReset(fixture))return 13;
    Widget*w=&context->state.widgets[0];
    w->used=1;w->id=7;w->kind=0;w->x=2;w->y=2;w->width=4;w->height=1;
    w->material=0;w->backgroundMaterial=-1;w->alpha=1;w->min=0;w->max=1;
    w->enabled=0;w->count=2;w->text[0]='D';w->text[1]='X';
    Indicator*q=&context->state.indicators[0];
    q->used=1;q->id=9;q->x=10;q->y=2;q->count=2;q->stepUs=1000;
    q->glyphs[0]='-';q->glyphs[1]='|';q->material=0;
    context->state.timeUs=1000;
    RegisteredState*r=&context->state.registeredStates[0];
    r->used=1;r->id=1;r->family=1;r->targetId=7;r->active=1;
    memcpy(r->role,"control",8);memcpy(r->path,"/app/disabled",14);
    characterTestRemember(fixture);
    context->clip=(ClipRect){0,0,(int)context->state.width,(int)context->state.height};
    Projection projection={0};
    nrDrawUI(context,&projection);
    width=context->state.width;
    unsigned disabled=2*width+2,indicator=2*width+10;
    if(context->cells[disabled].glyph!='D'||context->cells[disabled].id||
       context->characterOwners[disabled]!=((1u<<16)|7)||context->characterIndices[disabled]!=0)return 14;
    if(context->cells[indicator].glyph!='|'||context->cells[indicator].id||
       context->characterOwners[indicator]!=((6u<<16)|9)||context->characterIndices[indicator]!=1)return 15;
    if(context->characterOwner||!characterTestUnchanged(fixture))return 16;
    static Json json;static CharacterSelector selector;
    const char*filter="{\"role\":\"control\",\"path\":\"/app/disabled\",\"state\":\"disabled\",\"ids\":[0],\"indices\":[0],\"glyphs\":\"D\"}";
    if(!nrParse(&json,filter,(int)strlen(filter))||!nrCompileCharacterSelector(&json,0,&selector))return 19;
    if(!nrCharacterCellMatches(context,&selector,2,2)||nrCharacterCellMatches(context,&selector,3,2))return 20;
    if(nrCharacterCellMatches(context,&selector,-1,2)||nrCharacterCellMatches(context,&selector,(int)width,2))return 21;
    if(!characterTestUnchanged(fixture))return 22;
    NrCell savedCell=context->cells[disabled];
    uint32_t savedIndex=context->characterIndices[disabled],savedOwner=context->characterOwners[disabled];
    for(int repeat=0;repeat<32;repeat++)if(!nrCharacterCellMatches(context,&selector,2,2))return 23;
    if(memcmp(&savedCell,&context->cells[disabled],sizeof(savedCell))||
       savedIndex!=context->characterIndices[disabled]||savedOwner!=context->characterOwners[disabled])return 24;
    /* The historical component alias follows actual hit IDs, not semantic owners. */
    const char*component="{\"role\":\"component\"}";
    if(!nrParse(&json,component,(int)strlen(component))||!nrCompileCharacterSelector(&json,0,&selector))return 25;
    if(nrCharacterCellMatches(context,&selector,2,2))return 26;
    /* Removing a registered target makes its owner dormant, without repainting
     * the retained frame or treating its previous role/path as current. */
    w->used=0;
    const char*fallback="{\"role\":\"system-text\",\"path\":\"/screen/background\",\"state\":\"inactive\",\"indices\":[0]}";
    if(!nrParse(&json,fallback,(int)strlen(fallback))||!nrCompileCharacterSelector(&json,0,&selector))return 27;
    if(!nrCharacterCellMatches(context,&selector,2,2))return 28;
    w->used=1;
    /* Index fallback is viewport-local for primitives with no authored source. */
    context->characterIndices[disabled]=UINT32_MAX;
    memset(&selector,0,sizeof(selector));selector.hasIndices=1;selector.indexCount=1;selector.indices[0]=disabled;
    if(!nrCharacterCellMatches(context,&selector,2,2))return 29;
    context->characterIndices[disabled]=savedIndex;
    /* Plotted ink must clear any index from a previous text glyph. */
    w->kind=6;w->value=1;w->enabled=0;
    characterTestRemember(fixture);
    nrDrawUI(context,&projection);
    if(context->cells[disabled].id||context->characterOwners[disabled]!=((1u<<16)|7)||
       context->characterIndices[disabled]!=UINT32_MAX)return 17;
    if(context->characterOwner||!characterTestUnchanged(fixture))return 18;
    return 0;
}

int nrTestCharacterRender(void){return characterTestRun(characterRenderChecks);}
