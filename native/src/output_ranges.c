#include "internal.h"
/* Validate the bytes actually written, not unused caller capacity. Pure queries
 * must not turn context-owned authority or scratch into caller output. */
int nrExternalOutput(const NrContext*c,const void*out,size_t bytes){
    uintptr_t first=(uintptr_t)out,context=(uintptr_t)c;
    if(first>UINTPTR_MAX-bytes||context>UINTPTR_MAX-sizeof(*c))return 0;
    if(bytes&&first<context+sizeof(*c)&&context<first+bytes)return 0;
    uintptr_t prompt=(uintptr_t)c->promptMemory,render=(uintptr_t)c->cells;
    if(bytes&&c->promptMemoryBytes&&first<prompt+c->promptMemoryBytes&&prompt<first+bytes)return 0;
    if(bytes&&c->renderMemoryBytes&&first<render+c->renderMemoryBytes&&render<first+bytes)return 0;
    uintptr_t model=(uintptr_t)c->modelMemory;
    if(bytes&&c->modelMemoryBytes&&first<model+c->modelMemoryBytes&&model<first+bytes)return 0;
    uintptr_t modal=(uintptr_t)c->modalMemory;
    if(bytes&&c->modalMemoryBytes&&first<modal+c->modalMemoryBytes&&modal<first+bytes)return 0;
    return 1;
}
