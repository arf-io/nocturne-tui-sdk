#include "internal.h"

/* A view keeps old window runs at their immutable offsets while the prompt has
 * its own full-sized source and identity arrays. Metadata is copied explicitly. */
typedef struct {uint32_t id,count,generation,padding;uint32_t *source,*identities,*header,capacity;} IdentityView;
static IdentityView identityView(State*s,int slot){
    IdentityView q;
    if(!slot){memcpy(&q,&s->promptIdentity,16);q.source=s->promptIdentity.source;q.identities=s->promptIdentity.identities;q.header=&s->promptIdentity.id;q.capacity=s->dynamicPrompt.capacity;}
    else{TextIdentityRun*p=&s->textIdentities[slot];memcpy(&q,p,16);q.source=p->source;q.identities=p->identities;q.header=&p->id;q.capacity=NR_MAX_TEXT;}
    return q;
}
static void clearIdentity(IdentityView*q){q->id=q->count=q->generation=q->padding=0;memset(q->source,0,q->capacity*4);memset(q->identities,0,q->capacity*4);}
static void saveIdentity(IdentityView*q){memcpy(q->header,q,16);}

/* Canonical source mirrors let every input/trigger/scheduled edit reconcile in
 * native state, independent of host catch-up partition and render frequency. */
static const uint32_t*sourceAt(const State*s,int slot,uint32_t*id,uint32_t*count){
    if(!slot){if(s->promptDocument.count<0||s->promptDocument.count>(int)s->dynamicPrompt.capacity)return 0;*id=0;*count=s->promptDocument.count;return s->promptDocument.glyphs;}
    int title=slot>(int)NR_MAX_WINDOWS,index=(slot-1)%NR_MAX_WINDOWS;const Window*w=&s->windows[index];
    if(!w->used)return 0;int length=title?w->titleCount:w->textCount;
    if(length<0||length>(title?160:(int)NR_MAX_TEXT))return 0;*id=w->id;*count=length;return title?w->title:w->text;
}
typedef struct {State*state;uint32_t nextIdentity,nextGeneration;int enabled;} IdentityProbe;
/* Restore-only temporary identifiers are selected against all retained runs.
 * This uncommon exhaustion path has no fixed bitmap or generation bit width. */
static int allocateIdentity(State*s,IdentityProbe*probe,int generation,uint32_t*out){
    uint32_t*counter=generation?&s->nextTextRunGeneration:&s->nextClusterIdentity;
    if(*counter!=UINT32_MAX){*out=(*counter)++;return 1;}
    if(!probe||!probe->enabled)return 0;
    uint32_t*cursor=generation?&probe->nextGeneration:&probe->nextIdentity;
    while(*cursor<UINT32_MAX){uint32_t candidate=(*cursor)++;int used=0;
        for(int slot=0;slot<1+2*(int)NR_MAX_WINDOWS&&!used;slot++){IdentityView q=identityView(s,slot);
            if(generation)used=q.generation==candidate;
            else for(uint32_t k=0;k<q.count&&k<q.capacity;k++)if(q.identities[k]==candidate){used=1;break;}}
        if(!used){*out=candidate;return 1;}
    }return 0;
}
static int syncRun(State*s,IdentityView*q,const uint32_t*source,uint32_t id,uint32_t count,IdentityProbe*probe){
    if(!q->generation||q->id!=id){
        uint32_t generation;if(!allocateIdentity(s,probe,1,&generation))return 0;clearIdentity(q);q->id=id;q->generation=generation;
    }
    if(q->count==count&&!memcmp(q->source,source,count*4))return 1;
    size_t stride=(size_t)s->dynamicPrompt.capacity+1;
    uint32_t*oldBreaks=s->dynamicPrompt.scratch+14*stride,*newBreaks=oldBreaks+stride,*identities=newBreaks+stride;
    unsigned char*oldBoundary=(unsigned char*)(identities+stride),*newBoundary=oldBoundary+stride;
    memset(identities,0,stride*4);memset(oldBoundary,0,stride);memset(newBoundary,0,stride);
    int oldN=nrGraphemeBreaks(q->source,q->count,oldBreaks,(uint32_t)stride),newN=nrGraphemeBreaks(source,count,newBreaks,(uint32_t)stride);
    if(oldN<1||newN<1)return 0;
    for(int i=0;i<oldN;i++)oldBoundary[oldBreaks[i]]=1;for(int i=0;i<newN;i++)newBoundary[newBreaks[i]]=1;
    uint32_t prefix=0,suffix=0;while(prefix<q->count&&prefix<count&&q->source[prefix]==source[prefix])prefix++;
    while(suffix<q->count-prefix&&suffix<count-prefix&&q->source[q->count-1-suffix]==source[count-1-suffix])suffix++;
    while(prefix&&(!oldBoundary[prefix]||!newBoundary[prefix]))prefix--;
    while(suffix&&(!oldBoundary[q->count-suffix]||!newBoundary[count-suffix]))suffix--;
    for(int i=0;i<newN-1;i++){
        uint32_t begin=newBreaks[i],end=newBreaks[i+1],identity;
        if(end<=prefix)identity=q->identities[begin];
        else if(begin>=count-suffix)identity=q->identities[q->count-(count-begin)];
        else if(!allocateIdentity(s,probe,0,&identity))return 0;
        for(uint32_t k=begin;k<end;k++)identities[k]=identity;
    }
    memset(q->source,0,q->capacity*4);memcpy(q->source,source,count*4);memcpy(q->identities,identities,q->capacity*4);q->count=count;return 1;
}
static int syncIdentities(State*s,int probing){
    IdentityProbe probe={.state=s,.enabled=probing,.nextIdentity=1,.nextGeneration=1};
    if(!s->nextClusterIdentity)s->nextClusterIdentity=1;if(!s->nextTextRunGeneration)s->nextTextRunGeneration=1;
    for(int slot=0;slot<1+2*(int)NR_MAX_WINDOWS;slot++){
        uint32_t id=0,count=0;const uint32_t*source=sourceAt(s,slot,&id,&count);
        IdentityView q=identityView(s,slot);
        if(!source){if(!slot)return 0;clearIdentity(&q);saveIdentity(&q);continue;}
        if(!syncRun(s,&q,source,id,count,&probe))return 0;saveIdentity(&q);
    }return 1;
}
int nrSyncTextIdentities(State*s){int result=syncIdentities(s,0);if(result)nrPromptStorageMirror(s);return result;}
/* Slot 0 of syncIdentities alone, without the mirror: for a direct commit that changed the prompt's text and no
 * window document (TRANSACTIONS.md, "draft"). On a settled State every other slot is already a fixed point. */
int nrSyncPromptIdentity(State*s){
    uint32_t id=0,count=0;const uint32_t*source=sourceAt(s,0,&id,&count);
    if(!source||!s->nextClusterIdentity||!s->nextTextRunGeneration)return 0;
    IdentityView q=identityView(s,0);
    if(!syncRun(s,&q,source,id,count,NULL))return 0;
    saveIdentity(&q);return 1;
}
int nrProbeTextIdentities(NrContext*c,State*s){
    if(!c->checkingPending||s!=&c->probe)return 0;
    int result=syncIdentities(s,1);if(result)nrPromptStorageMirror(s);return result;
}
int nrValidTextIdentities(const State*s){
    if(s->schema<NR_STATE_SCHEMA_TEXT_IDENTITIES){
        if(s->nextClusterIdentity||s->nextTextRunGeneration)return 0;
        const unsigned char*bytes=(const unsigned char*)s->textIdentities;
        for(size_t i=0;i<sizeof(s->textIdentities);i++)if(bytes[i])return 0;return 1;
    }
    if(!s->nextClusterIdentity||!s->nextTextRunGeneration)return 0;
    size_t stride=(size_t)s->dynamicPrompt.capacity+1;uint32_t*seen=s->dynamicPrompt.scratch+24*stride;size_t seenCount=0,seenCapacity=40*stride;
    for(int slot=0;slot<1+2*(int)NR_MAX_WINDOWS;slot++){
        uint32_t id=0,count=0;const uint32_t*source=sourceAt(s,slot,&id,&count);IdentityView value=identityView((State*)s,slot);const IdentityView*q=&value;
        if(!source){if(!slot)return 0;if(q->id||q->count||q->generation||q->padding)return 0;for(uint32_t k=0;k<q->capacity;k++)if(q->source[k]||q->identities[k])return 0;continue;}
        if(q->padding||q->id!=id||q->count!=count||!q->generation||q->generation>=s->nextTextRunGeneration||memcmp(q->source,source,count*4))return 0;
        for(int earlier=0;earlier<slot;earlier++)if(identityView((State*)s,earlier).generation==q->generation)return 0;
        for(uint32_t k=count;k<q->capacity;k++)if(q->source[k]||q->identities[k])return 0;
        uint32_t*breaks=s->dynamicPrompt.scratch+14*stride;int n=nrGraphemeBreaks(source,count,breaks,(uint32_t)stride);if(n<1)return 0;
        for(int i=0;i<n-1;i++){
            uint32_t identity=q->identities[breaks[i]];if(!identity||identity>=s->nextClusterIdentity)return 0;
            for(uint32_t k=breaks[i];k<breaks[i+1];k++)if(q->identities[k]!=identity)return 0;
            if(seenCount==seenCapacity){nrPromptRequire((State*)s,s->dynamicPrompt.capacity*2ull);return 0;}seen[seenCount++]=identity;
        }
    }
    /* Heap sort uses the caller-owned scratch and cannot saturate a hash table. */
    for(size_t start=seenCount/2;start>0;){size_t root=--start;for(;;){size_t child=root*2+1;if(child>=seenCount)break;if(child+1<seenCount&&seen[child]<seen[child+1])child++;if(seen[root]>=seen[child])break;uint32_t v=seen[root];seen[root]=seen[child];seen[child]=v;root=child;}}
    for(size_t end=seenCount;end>1;){uint32_t v=seen[0];seen[0]=seen[--end];seen[end]=v;size_t root=0;for(;;){size_t child=root*2+1;if(child>=end)break;if(child+1<end&&seen[child]<seen[child+1])child++;if(seen[root]>=seen[child])break;v=seen[root];seen[root]=seen[child];seen[child]=v;root=child;}}
    for(size_t i=1;i<seenCount;i++)if(seen[i-1]==seen[i])return 0;return 1;
}
int nrTextRunClusters(const NrContext*c,uint32_t kind,uint32_t id,uint32_t*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||(!out&&capacity)||((uintptr_t)out%4))return -1;
    const uint32_t*source=0;IdentityView holder;const IdentityView*identity=0;const TextRun*animated=0;uint32_t count=0,generation=0;
    if(kind==0&&id==0){holder=identityView((State*)&c->state,0);identity=&holder;source=c->state.promptDocument.glyphs;count=c->state.promptDocument.count;}
    else if(kind==1){for(int i=0;i<NR_TEXTS;i++)if(c->state.text[i].used&&(uint32_t)c->state.text[i].id==id){animated=&c->state.text[i];source=animated->text;count=animated->count;break;}}
    else if(kind==2||kind==3){for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(c->state.windows[i].used&&(uint32_t)c->state.windows[i].id==id){holder=identityView((State*)&c->state,1+i+(kind==3?NR_MAX_WINDOWS:0));identity=&holder;source=identity->source;count=identity->count;break;}}
    if(!source)return -1;if(identity)generation=identity->generation;
    size_t stride=(size_t)c->state.dynamicPrompt.capacity+1;uint32_t*breaks=c->state.dynamicPrompt.scratch+14*stride;int n=nrGraphemeBreaks(source,count,breaks,(uint32_t)stride);if(n<1)return -1;n--;
    if(!out)return n;if(capacity<(uint32_t)n)return -1;
    uintptr_t first=(uintptr_t)out,context=(uintptr_t)c;size_t bytes=(size_t)n*16;
    if(first>UINTPTR_MAX-bytes||(first<context+sizeof(*c)&&context<first+bytes)||!nrExternalOutput(c,out,bytes))return -1;
    for(int i=0;i<n;i++){uint32_t row[4]={identity?identity->identities[breaks[i]]:animated->origin[breaks[i]].identity,breaks[i],breaks[i+1],generation};memcpy(out+4*i,row,sizeof(row));}return n;
}
