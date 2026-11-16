#include "nocturne_native.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    uint32_t bytes=nrContextSize();
    NrContext *scene=calloc(1,bytes);
    if(!scene || nrInit(scene,bytes,2030)!=0) return 1;
    const char *command="{\"op\":\"batch\",\"commands\":[{\"op\":\"resize\",\"width\":80,\"height\":24},{\"op\":\"widget\",\"id\":1,\"kind\":\"progress\",\"x\":5,\"y\":6,\"width\":60,\"height\":3,\"value\":0.65,\"border\":\"rounded\"}]}";
    if(nrCommand(scene,command,(uint32_t)strlen(command))<0) {
        fprintf(stderr,"%s\n",nrError(scene)); free(scene); return 2;
    }
    uint32_t count=nrRender(scene);
    if(count!=80*24 || !nrCells(scene)) {free(scene);return 3;}
    printf("%u x %u: %u cells\n",nrWidth(scene),nrHeight(scene),count);
    free(scene);return 0;
}
