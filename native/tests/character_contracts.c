#include <stdio.h>
int nrTestCharacterSelector(void);
int nrTestCharacterOwner(void);
int nrTestCharacterRender(void);
int nrTestCharacterPaint(void);
int nrTestCharacterEffects(void);
int nrTestCharacterRule(void);
int nrTestCharacterRegistry(void);
int nrTestCharacterRegion(void);
int main(void){
    int selector=nrTestCharacterSelector(),owner=nrTestCharacterOwner(),render=nrTestCharacterRender(),paint=nrTestCharacterPaint();
    printf("{\"selectorStatus\":%d,\"ownerStatus\":%d,\"renderStatus\":%d,\"paintStatus\":%d}\n",selector,owner,render,paint);
    int effects=nrTestCharacterEffects();
    printf("{\"effectsStatus\":%d}\n",effects);
    int rule=nrTestCharacterRule();printf("{\"ruleStatus\":%d}\n",rule);
    int registry=nrTestCharacterRegistry();printf("{\"registryStatus\":%d}\n",registry);
    int region=nrTestCharacterRegion();printf("{\"regionStatus\":%d}\n",region);
    return selector||owner||render||paint||effects||rule||registry||region;
}
