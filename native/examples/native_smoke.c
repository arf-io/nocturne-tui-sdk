#include "nocturne_native.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    uint32_t bytes=nrContextSize();
    void *memory=calloc(1,bytes);
    if (!memory||nrInit(memory,bytes,2030)) {free(memory);return 1;}
    NrContext *scene=memory;
    const char *input="{\"op\":\"input\",\"text\":\"Native C, no controller process.\"}";
    if(nrCommand(scene,input,(uint32_t)strlen(input))<0 || nrRender(scene)==0) {free(memory);return 2;}
    puts(nrInfo(scene));
    free(memory);
    return 0;
}
