#include "character_test_context.h"
/* Pure current-state ownership oracle; run at the complete API gate. */
static int characterOwnerChecks(CharacterTestContext*fixture){
    State*state=&fixture->context->state;
    state->widgets[0].used=1;state->widgets[0].id=7;state->widgets[0].enabled=1;state->widgets[0].active=1;
    RegisteredState*r=&state->registeredStates[0];r->used=1;r->id=19;r->family=1;r->targetId=7;r->active=1;
    memcpy(r->role,"control",8);memcpy(r->path,"/app/control",13);
    if(nrCharacterRegisteredOwner(state,NR_ID_WIDGET|7)!=r)return 1;
    if(nrCharacterRegisteredOwner(state,NR_ID_WIDGET|8))return 2;
    if(nrCharacterRegisteredOwner(state,0))return 3;
    state->widgets[0].used=0;if(nrCharacterRegisteredOwner(state,NR_ID_WIDGET|7))return 4;
    state->widgets[0].used=1;r->active=0;
    if(nrCharacterRegisteredOwner(state,NR_ID_WIDGET|7)!=r)return 5;
    if(nrRegisteredFlags(state,r)&1u)return 6;
    r->family=2;r->targetId=3;state->windows[0].used=1;state->windows[0].id=3;
    uint32_t chrome[]={NR_ID_WINDOW,NR_ID_DOCK,NR_ID_CLOSE,NR_ID_MIN,NR_ID_MAX};
    for(unsigned i=0;i<sizeof(chrome)/sizeof(chrome[0]);i++)if(nrCharacterRegisteredOwner(state,chrome[i]|3)!=r)return 7;
    r->family=4;r->targetId=13;state->text[0].used=1;state->text[0].id=13;
    if(nrCharacterSemanticOwner(state,(4u<<16)|13)!=r)return 8;
    if(nrCharacterSemanticOwner(state,(1u<<16)|13))return 9;
    state->text[0].used=0;if(nrCharacterSemanticOwner(state,(4u<<16)|13))return 10;
    state->text[0].used=1;r->active=0;
    if(nrCharacterSemanticOwner(state,(4u<<16)|13)!=r)return 11;
    if(nrCharacterSemanticOwner(state,0)||nrCharacterSemanticOwner(state,0xffff0000u))return 12;
    state->particles[0].state=1;state->particles[0].emitterId=27;
    if(nrCharacterFragmentOwner(state,0x20000001u)!=((3u<<16)|27))return 13;
    state->particles[0].state=0;if(nrCharacterFragmentOwner(state,0x20000001u))return 14;
    state->deposits[0].used=1;state->deposits[0].emitterId=28;
    if(nrCharacterFragmentOwner(state,0x30000001u)!=((3u<<16)|28))return 15;
    if(nrCharacterFragmentOwner(state,1)!=(8u<<16)||nrCharacterFragmentOwner(state,2)!=(9u<<16))return 16;
    if(nrCharacterFragmentOwner(state,0x2000ffffu)||nrCharacterFragmentOwner(state,0x41000001u))return 17;
    return 0;
}

int nrTestCharacterOwner(void){return characterTestRun(characterOwnerChecks);}
