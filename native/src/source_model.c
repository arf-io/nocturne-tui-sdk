#include "internal.h"
#include "scenic_native.h"
#include "scenic_source_raster.h"
#include "source_compositor.h"
#include <limits.h>
_Static_assert(sizeof(NrModelTriangle)==40,"Original model record ABI");
static int validContext(const NrContext*c){return c&&c->valid==NR_MAGIC&&c->capacity>=sizeof(*c);}
static int fail(NrContext*c,const char*m){if(c)memcpy(c->error,m,strlen(m)+1);return -1;}
static int recordsValid(const NrModelTriangle*t,uint32_t n){
    if(n&&!t)return 0;
    for(uint32_t i=0;i<n;i++){if(t[i].color>0xffffffu)return 0;for(unsigned k=0;k<9;k++)if(t[i].vertices[k]<-8388608||t[i].vertices[k]>8388608)return 0;}
    return 1;
}
uint64_t nrModelMemorySize(const NrContext*c){return validContext(c)?c->modelRequiredBytes:0;}
uint64_t nrModelMemoryCapacity(const NrContext*c){return validContext(c)?c->modelMemoryBytes:0;}
int nrModelRequire(State*s,uint32_t n){
    NrContext*c=s->dynamicPrompt.owner;if(!validContext(c))return 0;
    if(n<=c->modelCapacity)return 1;
    uint64_t cap=c->modelCapacity;while(cap<n){cap+=cap/2+1;if(cap>UINT32_MAX){cap=UINT32_MAX;break;}}
    uint64_t bytes=cap*3u*sizeof(NrModelTriangle);if(bytes>SIZE_MAX){fail(c,"Model storage address representation exhausted");return 0;}
    c->modelRequestedCapacity=(uint32_t)cap;c->modelRequiredBytes=bytes;fail(c,"Model storage required");return 0;
}
int nrSetModelMemory(NrContext*c,void*memory,uint64_t bytes){
    if(!validContext(c)||!memory||((uintptr_t)memory&7u)||bytes>SIZE_MAX||bytes>UINTPTR_MAX-(uintptr_t)memory||bytes<c->modelRequiredBytes||!nrExternalOutput(c,memory,(size_t)bytes))return -1;
    uint32_t cap=c->modelRequestedCapacity;if(cap<c->modelCapacity||!cap||(uint64_t)cap*3u*sizeof(NrModelTriangle)>bytes)return -1;
    c->settled=0;
    NrModelTriangle*base=memory;uint32_t count=c->state.sourceModel.count;
    if(count)memcpy(base,c->state.modelRecords,(size_t)count*sizeof(*base));
    /* A rebind is permitted only outside a mutation. Scratch views restart at
     * the committed geometry; no pointer from the old arena remains. */
    c->state.modelRecords=base;c->trial.modelRecords=base+cap;c->probe.modelRecords=base+2u*(size_t)cap;
    if(count){memcpy(c->trial.modelRecords,base,(size_t)count*sizeof(*base));memcpy(c->probe.modelRecords,base,(size_t)count*sizeof(*base));}
    c->trial.sourceModel=c->state.sourceModel;c->probe.sourceModel=c->state.sourceModel;
    c->modelMemory=memory;c->modelMemoryBytes=bytes;c->modelCapacity=cap;c->modelRequiredBytes=(uint64_t)cap*3u*sizeof(*base);return 0;
}
void nrModelCopyState(State*dst,const State*src){if(src->sourceModel.count)memcpy(dst->modelRecords,src->modelRecords,(size_t)src->sourceModel.count*sizeof(NrModelTriangle));}
uint32_t nrModelTriangleCount(const NrContext*c){return validContext(c)?c->state.sourceModel.count:0;}
int nrModelCopy(const NrContext*c,NrModelTriangle*out,uint32_t cap){
    if(!validContext(c))return -1;uint32_t n=c->state.sourceModel.count;uint64_t bytes=(uint64_t)n*sizeof(*out);
    if(n>INT32_MAX||cap<n||bytes>SIZE_MAX||(n&&!out)||!nrExternalOutput(c,out,(size_t)bytes))return -1;
    if(n)memcpy(out,c->state.modelRecords,(size_t)bytes);return (int)n;
}
int nrModelSet(NrContext*c,const NrModelTriangle*t,uint32_t count){
    if(!validContext(c))return -1;c->error[0]=0;c->settled=0;
    uint64_t bytes=(uint64_t)count*sizeof(*t),wire=24u+(uint64_t)offsetof(State,dynamicPrompt)+nrPromptPayloadSize(&c->state)+bytes+(uint64_t)c->state.sourceModal.scalars*4;
    if(wire>UINT32_MAX||bytes>SIZE_MAX||(count&&!t)||((uintptr_t)t&3u)||!nrExternalOutput(c,t,(size_t)bytes)||!recordsValid(t,count))return fail(c,"Invalid source model records");
    if(!nrModelRequire(&c->state,count))return -1;
    nrStateCopy(&c->trial,&c->state);if(count)memcpy(c->trial.modelRecords,t,(size_t)bytes);c->trial.sourceModel.count=count;
    if(!nrCountedValidState(c,&c->trial))return fail(c,"Source model state rejected");
    nrStateCopy(&c->state,&c->trial);c->characterFrameValid=0;return 0;
}
int nrValidSourceModel(const State*s){
    const NrContext*c=s->dynamicPrompt.owner;
    if(s->sourceModel.reserved||s->sourceModel.view.used>1||s->sourceModel.view.hasWorldDetail>1)return 0;
    if(s->schema<NR_STATE_SCHEMA_SOURCE_MODEL){const unsigned char*p=(const unsigned char*)&s->sourceModel;for(size_t i=0;i<sizeof(s->sourceModel);i++)if(p[i])return 0;return 1;}
    if(!validContext(c)||s->sourceModel.count>c->modelCapacity||!recordsValid(s->modelRecords,s->sourceModel.count))return 0;
    if(!s->sourceModel.view.used){static const SceneArt empty={0};return !memcmp(&s->sourceModel.view,&empty,sizeof(empty));}
    NrScenicArtConfig q;memcpy(q.world,s->sourceModel.view.world,sizeof(q.world));memcpy(q.detail,s->sourceModel.view.detail,sizeof(q.detail));q.hasWorldDetail=(uint8_t)s->sourceModel.view.hasWorldDetail;return nrScenicArtValidate(&q);
}
int nrModelLoadPayload(State*s,const uint8_t*p,uint32_t bytes){
    uint32_t n=s->sourceModel.count;if((uint64_t)n*sizeof(NrModelTriangle)!=bytes)return -1;
    /* Snapshot byte buffers need no record alignment. Validate through aligned
     * locals before allocation or any authoritative geometry is replaced. */
    for(uint32_t i=0;i<n;i++){NrModelTriangle t;memcpy(&t,p+(size_t)i*sizeof(t),sizeof(t));if(!recordsValid(&t,1))return -1;}
    if(!nrModelRequire(s,n))return -1;if(bytes)memcpy(s->modelRecords,p,bytes);return 0;
}
static void sample(void*user,int32_t x,int32_t y,int32_t depth,uint32_t rgb,int32_t alpha,int32_t threshold){nrSourcePixel(user,x,y,depth,rgb,alpha,threshold);}
int nrSourceModelDraw(NrContext*c,const State*s,int width,int height){
    if(!s->sourceModel.view.used)return 1;NrScenicArtConfig q;
    if(!nrSourceModelEffective(s,width,height,&q))return 0;
    /* A concurrently active source scene owns the common source sampling.
     * model-view rejects incompatible sampling, so both depth sets compose. */
    if(!c->sourceActive&&!nrSourceBegin(c,width,height,q.world[NR_WORLD_SAMPLING],q.world[NR_WORLD_PROJECTION],q.world[NR_WORLD_BACKGROUND]))return 0;
    NrScenicSourceRaster raster;if(!nrScenicSourceRasterInit(&raster,&q,width,height,sample,c))return 0;
    const NrScenicArtSink*sink=nrScenicSourceRasterSink(&raster);
    for(uint32_t i=0;i<s->sourceModel.count;i++){const NrModelTriangle*t=&s->modelRecords[i];const int32_t*v=t->vertices;sink->triangle(sink->user,v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],t->color,1000);}
    return 1;
}
