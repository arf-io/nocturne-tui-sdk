#include "internal.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static void* grow(NrContext*c,void*old){uint64_t n=nrModelMemorySize(c);void*p=malloc((size_t)n);assert(p);assert(nrSetModelMemory(c,p,n)==0);free(old);return p;}
int main(void){
 NrContext*a=malloc(nrContextSize()),*b=malloc(nrContextSize());assert(a&&b);assert(!nrInit(a,nrContextSize(),2030)&&!nrInit(b,nrContextSize(),2030));
 NrModelTriangle triangles[2]={{{-256,-256,0,256,-256,0,0,256,0},0x00ff00},{{-512,-512,256,512,-512,256,0,512,256},0xff0000}};
 assert(nrModelSet(a,triangles,1)==-1&&!strcmp(nrError(a),"Model storage required"));void*am=grow(a,0);assert(!nrModelSet(a,triangles,1));
 assert(a->state.modelRecords!=a->trial.modelRecords&&a->state.modelRecords!=a->probe.modelRecords&&a->trial.modelRecords!=a->probe.modelRecords);
 assert(nrModelSet(a,triangles,2)==-1);am=grow(a,am);assert(a->state.sourceModel.count==1&&a->trial.sourceModel.count==1&&a->probe.sourceModel.count==1);assert(!nrModelSet(a,triangles,2));
 nrStateCopy(&a->probe,&a->state);a->probe.modelRecords[0].color=0x123456;assert(a->state.modelRecords[0].color==0x00ff00&&a->trial.modelRecords[0].color==0x00ff00);
 uint32_t size=nrSnapshotSizeFor(a);unsigned char*wire=malloc(size),*unaligned=malloc((size_t)size+1),*before=malloc(size);assert(wire&&unaligned&&before);assert(!nrSave(a,wire,size));memcpy(unaligned+1,wire,size);
 assert(nrSetModelMemory(a,a,nrModelMemorySize(a))==-1);assert(nrSetModelMemory(a,(char*)am+8,nrModelMemorySize(a))==-1);assert(nrModelSet(a,a->state.modelRecords,2)==-1);assert(nrModelCopy(a,a->probe.modelRecords,2)==-1);
 assert(nrSetRenderMemory(a,am,nrRenderMemorySize(a))==-1);assert(nrSetPromptMemory(a,am,nrModelMemorySize(a))==-1);
 memcpy(before,wire,size);triangles[0].color=0x1000000;assert(nrModelSet(a,triangles,2)==-1);assert(!nrSave(a,wire,size));assert(!memcmp(before,wire,size));
 assert(nrLoad(b,unaligned+1,size)==-1);assert(!strcmp(nrError(b),"Model storage required"));void*bm=grow(b,0);assert(!nrLoad(b,unaligned+1,size));assert(!nrSave(b,wire,size));assert(!memcmp(before,wire,size));
 assert(nrModelSet(b,0,0)==0&&nrModelTriangleCount(b)==0);assert(nrModelTriangleCount(a)==2);assert(nrModelCopy(b,0,0)==0);
 free(am);free(bm);free(wire);free(unaligned);free(before);free(a);free(b);puts("PASS: distinct model arenas, growth, original state rollback, cross-alias rejection, unaligned snapshot restore, empty upload");return 0;
}
