#include "internal.h"
#include <stdio.h>
int main(void){
 printf("{\"schema\":%u,\"maxWindows\":%u,\"windowOffset\":%zu,\"windowSize\":%zu,\"usedOffset\":%zu,\"copies\":[",NR_STATE_SCHEMA,NR_MAX_WINDOWS,offsetof(State,windows),sizeof(Window),offsetof(Window,used));
#if NR_MAX_WINDOWS > 12
 printf("[%zu,%zu,%zu],[%zu,%zu,%zu],[%zu,%zu,%zu],[%zu,%zu,%zu],[%zu,%zu,%zu],[%zu,%zu,%zu]",offsetof(State,legacyWindows),offsetof(State,windows),sizeof(((State*)0)->legacyWindows),offsetof(State,legacyWindowSourceGeometry),offsetof(State,windowSourceGeometry),sizeof(((State*)0)->legacyWindowSourceGeometry),offsetof(State,legacyWindowPresentation),offsetof(State,windowPresentation),sizeof(((State*)0)->legacyWindowPresentation),offsetof(State,legacyWindowSourceOrder),offsetof(State,windowSourceOrder),sizeof(((State*)0)->legacyWindowSourceOrder),offsetof(State,legacyTextIdentities),offsetof(State,textIdentities),13*sizeof(TextIdentityRun),offsetof(State,legacyTextIdentities)+13*sizeof(TextIdentityRun),offsetof(State,textIdentities)+(1+NR_MAX_WINDOWS)*sizeof(TextIdentityRun),12*sizeof(TextIdentityRun));
#endif
 puts("]}");return 0;
}
