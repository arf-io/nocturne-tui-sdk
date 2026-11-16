#include "internal.h"
#include "catalog.inc"
const char *nrCatalogue(void) {
    return CATALOGUE;
}
int nrEffectId(const char*s) {
    for(unsigned i=0; i<sizeof(EFFECTS)/sizeof(EFFECTS[0]); i++)if(!strcmp(s,EFFECTS[i].id))return (int)i;
    return -1;
}
int nrEffectFamily(int e) {
    return e>=0&&e<(int)(sizeof(EFFECTS)/sizeof(EFFECTS[0]))?EFFECTS[e].family:-1;
}
int nrEffectAlgorithm(int e) {
    return e>=0&&e<(int)(sizeof(EFFECTS)/sizeof(EFFECTS[0]))?EFFECTS[e].algorithm:-1;
}
const char *nrEffectName(int e) {
    return e>=0&&e<(int)(sizeof(EFFECTS)/sizeof(EFFECTS[0]))?EFFECTS[e].id:"unknown";
}

int nrEffectProfile(int e) {
    return e>=0&&e<(int)(sizeof(EFFECTS)/sizeof(EFFECTS[0]))?EFFECTS[e].profile:0;
}
