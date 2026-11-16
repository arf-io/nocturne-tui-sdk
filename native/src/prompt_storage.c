#include "internal.h"
#include <limits.h>
/* Wire prefix contains only the historical fixed records. Runtime views and
 * caller-owned buffers never enter snapshots. */
static uint32_t **arrayAt(PromptRuntime*r,unsigned i){
    if(!i)return &r->document.glyphs;if(i<=100)return &r->document.undo[i-1];
    if(i==101)return &r->register0.glyphs;if(i<128)return &r->registers.slots[i-102].glyphs;
    if(i==128)return &r->identity.source;if(i==129)return &r->identity.identities;return &r->checkpoint;
}
static uint32_t arrayCount(const State*s,unsigned i){
    const PromptRuntime*r=&s->dynamicPrompt;
    if(!i)return (uint32_t)r->document.count;if(i<=100)return (uint32_t)r->document.undoCount[i-1];
    if(i==101)return (uint32_t)r->register0.count;if(i<128)return (uint32_t)r->registers.slots[i-102].count;
    if(i<130)return r->identity.count;return s->promptFramed.checkpointCount;
}
static uint64_t historyWords(const Prompt*p){uint64_t n=0;for(int i=0;i<NR_PROMPT_HISTORY;i++)n+=(uint32_t)p->undoCount[i];return n;}
static void historyBind(Prompt*p,uint32_t*base){for(int i=0;i<NR_PROMPT_HISTORY;i++){p->undo[i]=base;base+=(uint32_t)p->undoCount[i];}}
static uint64_t arenaBytes(uint32_t capacity,uint64_t history){return (((uint64_t)capacity+1)*(3u*(NR_PROMPT_DATA_ARRAYS+NR_PROMPT_SCRATCH_ARRAYS)+2u)+4*history)*4;}
static void bindRuntime(PromptRuntime*r,uint32_t*base,uint32_t cap,uint64_t history,NrContext*c){
    memset(r,0,sizeof(*r));r->capacity=cap;r->owner=c;size_t stride=(size_t)cap+1;
    r->document.glyphs=base;r->historyCapacity=history;historyBind(&r->document,base+(NR_PROMPT_DATA_ARRAYS+NR_PROMPT_SCRATCH_ARRAYS)*stride);
    for(unsigned i=101;i<NR_PROMPT_WIRE_ARRAYS;i++)*arrayAt(r,i)=base+(size_t)(i-100)*stride;
    r->scratch=base+(size_t)NR_PROMPT_DATA_ARRAYS*stride;r->scratchWords=(cap+1u)*NR_PROMPT_SCRATCH_ARRAYS;
}
void nrPromptCopy(Prompt*dst,const Prompt*src){
    uint32_t*glyphs=dst->glyphs,*history=dst->undo[0];*dst=*src;dst->glyphs=glyphs;historyBind(dst,history);
    memcpy(glyphs,src->glyphs,(size_t)src->count*4);memcpy(history,src->undo[0],(size_t)historyWords(src)*4);
}
/* Returns the arena bytes written: history words, used data-array words and their zero-filled tails. */
static uint64_t copyRuntime(State*dst,const State*src){
    PromptRuntime bindings=dst->dynamicPrompt;dst->dynamicPrompt=src->dynamicPrompt;
    dst->dynamicPrompt.capacity=bindings.capacity;dst->dynamicPrompt.historyCapacity=bindings.historyCapacity;dst->dynamicPrompt.owner=bindings.owner;
    dst->dynamicPrompt.scratch=bindings.scratch;dst->dynamicPrompt.scratchWords=bindings.scratchWords;
    historyBind(&dst->dynamicPrompt.document,bindings.document.undo[0]);
    uint64_t bytes=historyWords(&src->dynamicPrompt.document)*4;
    memcpy(bindings.document.undo[0],src->dynamicPrompt.document.undo[0],(size_t)historyWords(&src->dynamicPrompt.document)*4);
    for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++){
        if(i>0&&i<=100)continue;
        uint32_t*target=*arrayAt(&bindings,i),*source=*arrayAt((PromptRuntime*)&src->dynamicPrompt,i),n=arrayCount(src,i);
        *arrayAt(&dst->dynamicPrompt,i)=target;if(n)memmove(target,source,(size_t)n*4);
        if(n<bindings.capacity)memset(target+n,0,(size_t)(bindings.capacity-n)*4);
        bytes+=(uint64_t)(n<bindings.capacity?bindings.capacity:n)*4;
    }
    return bytes;
}
void nrStateCopy(State*dst,const State*src){
    if(dst==src)return;
    memcpy(dst,src,offsetof(State,dynamicPrompt));uint64_t runtime=copyRuntime(dst,src);nrModelCopyState(dst,src);nrModalCopyState(dst,src);
    /* Counted in the copy primitive, against the context that owns the destination (section 5.6). */
    nrCountStateCopy(dst->dynamicPrompt.owner,runtime+(uint64_t)src->sourceModel.count*sizeof(NrModelTriangle)+(uint64_t)src->sourceModal.scalars*4);
}
void nrPromptRuntimeClear(State*s){
    PromptRuntime binding=s->dynamicPrompt;
    bindRuntime(&s->dynamicPrompt,binding.document.glyphs,binding.capacity,binding.historyCapacity,binding.owner);
    memset(binding.document.glyphs,0,(size_t)NR_PROMPT_DATA_ARRAYS*((size_t)binding.capacity+1)*4);
}
static void bindContext(NrContext*c,uint32_t*memory,uint32_t cap,uint64_t history){
    size_t stride=(size_t)(NR_PROMPT_DATA_ARRAYS+NR_PROMPT_SCRATCH_ARRAYS)*(cap+1u)+(size_t)history;
    bindRuntime(&c->state.dynamicPrompt,memory,cap,history,c);bindRuntime(&c->trial.dynamicPrompt,memory+stride,cap,history,c);bindRuntime(&c->probe.dynamicPrompt,memory+2*stride,cap,history,c);
    uint32_t*backup=memory+3*stride;c->promptResetBackup.glyphs=backup;
    for(int i=0;i<NR_PROMPT_HISTORY;i++)c->promptResetBackup.undo[i]=backup+(cap+1u);
    c->promptCheckpointBackup=backup+(cap+1u)+(size_t)history;
    c->documentLayout=c->state.dynamicPrompt.scratch;c->documentClip=c->documentLayout+(size_t)(cap+1u)*5;
    c->promptMemoryCapacity=c->promptRequestedCapacity=cap;c->promptHistoryWords=c->promptRequestedHistoryWords=history;
}
void nrPromptBindInitial(NrContext*c){bindContext(c,c->inlinePromptMemory,NR_INLINE_PROMPT_CAPACITY,16u*(NR_INLINE_PROMPT_CAPACITY+1u));c->promptMemory=c->inlinePromptMemory;c->promptMemoryBytes=sizeof(c->inlinePromptMemory);c->promptRequiredBytes=c->promptMemoryBytes;}
uint64_t nrPromptMemorySize(const NrContext*c){return c&&c->valid==NR_MAGIC?c->promptRequiredBytes:0;}
uint64_t nrPromptMemoryCapacity(const NrContext*c){return c&&c->valid==NR_MAGIC?arenaBytes(c->promptMemoryCapacity,c->promptHistoryWords):0;}
static int overlaps(uintptr_t a,uint64_t an,uintptr_t b,uint64_t bn){return a<b+bn&&b<a+an;}
int nrSetPromptMemory(NrContext*c,void*memory,uint64_t bytes){
    if(!c||c->valid!=NR_MAGIC||!memory||((uintptr_t)memory&7u)||bytes>SIZE_MAX||bytes>UINTPTR_MAX-(uintptr_t)memory||bytes<c->promptRequiredBytes)return -1;
    if(overlaps((uintptr_t)memory,bytes,(uintptr_t)c,sizeof(*c))||overlaps((uintptr_t)memory,bytes,(uintptr_t)c->promptMemory,c->promptMemoryBytes)||overlaps((uintptr_t)memory,bytes,(uintptr_t)c->cells,c->renderMemoryBytes)||overlaps((uintptr_t)memory,bytes,(uintptr_t)c->modelMemory,c->modelMemoryBytes)||overlaps((uintptr_t)memory,bytes,(uintptr_t)c->modalMemory,c->modalMemoryBytes))return -1;
    uint32_t cap=c->promptRequestedCapacity;uint64_t history=c->promptRequestedHistoryWords;
    if(arenaBytes(cap,history)>bytes||cap<c->promptMemoryCapacity||history<c->promptHistoryWords)return -1;
    c->settled=0;
    PromptRuntime old=c->state.dynamicPrompt;
    bindContext(c,memory,cap,history);PromptRuntime fresh=c->state.dynamicPrompt;
    c->state.dynamicPrompt=old;c->trial.dynamicPrompt=fresh;copyRuntime(&c->trial,&c->state);c->state.dynamicPrompt=c->trial.dynamicPrompt;
    size_t stride=(size_t)(NR_PROMPT_DATA_ARRAYS+NR_PROMPT_SCRATCH_ARRAYS)*(cap+1u)+(size_t)history;
    bindRuntime(&c->trial.dynamicPrompt,(uint32_t*)memory+stride,cap,history,c);
    c->promptMemory=memory;c->promptMemoryBytes=bytes;c->promptRequiredBytes=arenaBytes(cap,history);return 0;
}
int nrPromptRequire(State*s,uint64_t needed){
    if(needed<=s->dynamicPrompt.capacity)return 1;
    NrContext*c=s->dynamicPrompt.owner;if(!c||needed>INT32_MAX){if(c)memcpy(c->error,"Prompt index representation exhausted",sizeof("Prompt index representation exhausted"));return 0;}
    uint64_t grown=s->dynamicPrompt.capacity;while(grown<needed){grown+=grown/2+1;if(grown>INT32_MAX){grown=INT32_MAX;break;}}
    grown|=1u;c->promptRequestedCapacity=(uint32_t)grown;c->promptRequiredBytes=arenaBytes((uint32_t)grown,c->promptRequestedHistoryWords);memcpy(c->error,"Prompt storage required",sizeof("Prompt storage required"));return 0;
}
static int historyRequire(State*s,uint64_t needed){
    if(needed<=s->dynamicPrompt.historyCapacity)return 1;NrContext*c=s->dynamicPrompt.owner;
    uint64_t grown=s->dynamicPrompt.historyCapacity;while(grown<needed)grown+=grown/2+1;grown=(grown+1)&~1ull;
    c->promptRequestedHistoryWords=grown;c->promptRequiredBytes=arenaBytes(c->promptRequestedCapacity,grown);
    memcpy(c->error,"Prompt storage required",sizeof("Prompt storage required"));return 0;
}
int nrPromptHistorySet(State*s,int slot,const uint32_t*text,int count,int caret){
    Prompt*p=&s->promptDocument;uint64_t total=historyWords(p),next=total-(uint32_t)p->undoCount[slot]+(uint32_t)count;
    if(!historyRequire(s,next))return 0;
    uint32_t*base=p->undo[0];size_t offset=(size_t)(p->undo[slot]-base),old=(uint32_t)p->undoCount[slot];
    memmove(base+offset+count,base+offset+old,(size_t)(total-offset-old)*4);
    if(count)memcpy(base+offset,text,(size_t)count*4);
    if(next<total)memset(base+(size_t)next,0,(size_t)(total-next)*4);
    p->undoCount[slot]=count;p->undoCaret[slot]=caret;historyBind(p,base);return 1;
}
int nrPromptAllowed(const State*s,uint64_t count){return count<=INT32_MAX&&(!s->promptFramed.options.maxChars||count<=s->promptFramed.options.maxChars);}
int nrPromptDecodeCommand(State*s,const Json*j,int token,uint32_t**out){
    int n=nrDecode(j,token,NULL,0);if(n<0)return -1;if(!nrPromptRequire(s,(uint32_t)n))return -1;
    *out=s->dynamicPrompt.scratch;return nrDecode(j,token,*out,(int)s->dynamicPrompt.capacity);
}
/* Metadata uses a compact fixed, pointer-free shape; scalar arrays follow in
 * explicit order and contain exactly their used lengths. */
typedef struct {
    int32_t count,caret,anchor,mode,active,minRows,maxRows,border,padding,vimMode;double alpha;
    int32_t undoCount[16],undoCaret[16],undoHead,undoSize,modal;uint32_t pad;uint64_t revision;
    int32_t registers[27][2],pending,selected,append,padding2;uint64_t registerRevision;
    uint32_t identity[4],lengths[47];
} PromptWire73;
typedef struct {
    int32_t count,caret,anchor,mode,active,minRows,maxRows,border,padding,vimMode;double alpha;
    int32_t undoCount[100],undoCaret[100],undoHead,undoSize,modal;uint32_t pad;uint64_t revision;
    int32_t registers[27][2],pending,selected,append,padding2;uint64_t registerRevision;
    uint32_t identity[4],lengths[NR_PROMPT_WIRE_ARRAYS];
} PromptWire;
uint32_t nrPromptWireSize(void){return (uint32_t)sizeof(PromptWire);}
static void wireFrom(const State*s,PromptWire*w){
    memset(w,0,sizeof(*w));const Prompt*p=&s->promptDocument;
    memcpy(&w->count,&p->count,offsetof(Prompt,undo)-offsetof(Prompt,count));
    memcpy(w->undoCount,p->undoCount,sizeof(w->undoCount));memcpy(w->undoCaret,p->undoCaret,sizeof(w->undoCaret));w->undoHead=p->undoHead;w->undoSize=p->undoSize;w->modal=p->modal;w->revision=p->revision;
    for(int i=0;i<27;i++){const PromptRegister*r=i?&s->promptRegisters.slots[i-1]:&s->promptRegister;w->registers[i][0]=r->count;w->registers[i][1]=r->linewise;}
    w->pending=s->promptRegisters.pending;w->selected=s->promptRegisters.selected;w->append=s->promptRegisters.append;w->padding2=s->promptRegisters.padding;w->registerRevision=s->promptRegisters.revision;
    memcpy(w->identity,&s->promptIdentity,16);for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++)w->lengths[i]=arrayCount(s,i);
}
uint32_t nrPromptPayloadSize(const State*s){uint64_t n=sizeof(PromptWire);for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++)n+=(uint64_t)arrayCount(s,i)*4;return n>UINT32_MAX?0:(uint32_t)n;}
int nrPromptSavePayload(const State*s,uint8_t*out,uint32_t cap){
    uint32_t size=nrPromptPayloadSize(s);if(!size||cap<size)return -1;PromptWire wire;wireFrom(s,&wire);memcpy(out,&wire,sizeof(wire));out+=sizeof(wire);
    for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++){uint32_t n=arrayCount(s,i);memcpy(out,*arrayAt((PromptRuntime*)&s->dynamicPrompt,i),(size_t)n*4);out+=(size_t)n*4;}return 0;
}
int nrPromptPayloadShape(const uint8_t*in,uint32_t bytes,uint32_t schema){
    uint64_t total;uint32_t lengths[NR_PROMPT_WIRE_ARRAYS],arrays;
    if(schema==NR_STATE_SCHEMA_DYNAMIC_PROMPT||schema==NR_STATE_SCHEMA_KINETIC_PAINT){
        if(bytes<sizeof(PromptWire73))return 0;PromptWire73 w;memcpy(&w,in,sizeof(w));if(w.pad)return 0;
        total=sizeof(w);arrays=47;memcpy(lengths,w.lengths,sizeof(w.lengths));
    }else{
        if(bytes<sizeof(PromptWire))return 0;PromptWire w;memcpy(&w,in,sizeof(w));if(w.pad)return 0;
        total=sizeof(w);arrays=NR_PROMPT_WIRE_ARRAYS;memcpy(lengths,w.lengths,sizeof(w.lengths));
    }
    for(unsigned i=0;i<arrays;i++){if(lengths[i]>INT32_MAX)return 0;total+=(uint64_t)lengths[i]*4;}
    return total==bytes;
}
int nrPromptLoadPayload(State*s,const uint8_t*in,uint32_t bytes,uint32_t schema){
    PromptWire w;memset(&w,0,sizeof(w));PromptWire73 old;int legacy=schema==NR_STATE_SCHEMA_DYNAMIC_PROMPT||schema==NR_STATE_SCHEMA_KINETIC_PAINT;uint32_t header=legacy?sizeof(old):sizeof(w),wireArrays=legacy?47:NR_PROMPT_WIRE_ARRAYS;
    if(bytes<header)return -1;
    unsigned mapping[NR_PROMPT_WIRE_ARRAYS];for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++)mapping[i]=i;
    if(legacy){
        memcpy(&old,in,sizeof(old));if(old.undoSize<0||old.undoSize>16||old.undoHead<0||old.undoHead>=16||s->editorRedo.count<0||s->editorRedo.count+old.undoSize>16)return -1;
        memcpy(&w.count,&old.count,48);w.undoHead=old.undoSize;w.undoSize=old.undoSize;w.modal=old.modal;w.pad=old.pad;w.revision=old.revision;
        memcpy(w.registers,old.registers,sizeof(w.registers));w.pending=old.pending;w.selected=old.selected;w.append=old.append;w.padding2=old.padding2;w.registerRevision=old.registerRevision;memcpy(w.identity,old.identity,16);
        w.lengths[0]=old.lengths[0];mapping[0]=0;
        for(int i=0;i<16;i++)mapping[i+1]=UINT32_MAX;
        for(int k=0;k<old.undoSize+s->editorRedo.count;k++){int i=(old.undoHead-old.undoSize+k+16)%16;w.undoCount[k]=old.undoCount[i];w.undoCaret[k]=old.undoCaret[i];w.lengths[k+1]=old.lengths[i+1];mapping[i+1]=k+1;}
        for(unsigned i=17;i<47;i++){w.lengths[i+84]=old.lengths[i];mapping[i]=i+84;}
    }else memcpy(&w,in,sizeof(w));
    uint64_t total=header,maximum=0,history=0;
    for(unsigned i=0;i<wireArrays;i++){uint32_t n=legacy?old.lengths[i]:w.lengths[i];if(n>INT32_MAX)return -1;total+=(uint64_t)n*4;}
    for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++){if(w.lengths[i]>maximum)maximum=w.lengths[i];if(i>0&&i<=100)history+=w.lengths[i];}
    if(total!=bytes||w.pad)return -1;
    if(w.count<0||(uint32_t)w.count!=w.lengths[0])return -1;
    for(int i=0;i<100;i++)if(w.undoCount[i]<0||(uint32_t)w.undoCount[i]!=w.lengths[i+1]||w.undoCaret[i]<0||w.undoCaret[i]>w.undoCount[i])return -1;
    if(legacy)for(int i=0;i<16;i++)if(old.undoCount[i]<0||(uint32_t)old.undoCount[i]!=old.lengths[i+1]||old.undoCaret[i]<0||old.undoCaret[i]>old.undoCount[i])return -1;
    if(!nrPromptRequire(s,maximum)||!historyRequire(s,history))return -2;
    nrPromptRuntimeClear(s);Prompt*p=&s->promptDocument;memcpy(&p->count,&w.count,offsetof(Prompt,undo)-offsetof(Prompt,count));
    memcpy(p->undoCount,w.undoCount,sizeof(w.undoCount));memcpy(p->undoCaret,w.undoCaret,sizeof(w.undoCaret));p->undoHead=w.undoHead;p->undoSize=w.undoSize;p->modal=w.modal;p->revision=w.revision;
    historyBind(p,p->undo[0]);
    for(int i=0;i<27;i++){PromptRegister*r=i?&s->promptRegisters.slots[i-1]:&s->promptRegister;r->count=w.registers[i][0];r->linewise=w.registers[i][1];}
    s->promptRegisters.pending=w.pending;s->promptRegisters.selected=w.selected;s->promptRegisters.append=w.append;s->promptRegisters.padding=w.padding2;s->promptRegisters.revision=w.registerRevision;memcpy(&s->promptIdentity,w.identity,16);
    for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++)if(arrayCount(s,i)!=w.lengths[i])return -1;
    in+=header;for(unsigned i=0;i<wireArrays;i++){uint32_t n=legacy?old.lengths[i]:w.lengths[i];if(mapping[i]!=UINT32_MAX)memcpy(*arrayAt(&s->dynamicPrompt,mapping[i]),in,(size_t)n*4);in+=(size_t)n*4;}
    if(legacy)nrPromptStorageMirror(s);return 0;
}
static void smallPromptFill(const Prompt*p,LegacyPrompt*q){
    memcpy(&q->count,&p->count,offsetof(Prompt,undo)-offsetof(Prompt,count));
    q->undoSize=p->undoSize<16?p->undoSize:16;q->undoHead=q->undoSize%16;q->modal=p->modal;q->revision=p->revision;
    if(p->count<=(int)NR_MAX_TEXT)memcpy(q->glyphs,p->glyphs,(size_t)p->count*4);else{q->count=q->caret=0;q->anchor=-1;}
    for(int k=0;k<q->undoSize;k++){int i=(p->undoHead-q->undoSize+k+NR_PROMPT_HISTORY)%NR_PROMPT_HISTORY;
        if(p->undoCount[i]<=(int)NR_MAX_TEXT){q->undoCount[k]=p->undoCount[i];q->undoCaret[k]=p->undoCaret[i];memcpy(q->undo[k],p->undo[i],(size_t)p->undoCount[i]*4);}}
}
static void smallPrompt(const Prompt*p,LegacyPrompt*q){memset(q,0,sizeof(*q));smallPromptFill(p,q);}
static void mirrorRedo(State*s){
    if(s->promptDocument.undoSize+s->editorRedo.count<=16)for(int k=0;k<s->editorRedo.count;k++){int i=(s->promptDocument.undoHead+k)%NR_PROMPT_HISTORY,j=(s->prompt.undoHead+k)%16;
        if(s->promptDocument.undoCount[i]<=(int)NR_MAX_TEXT){s->prompt.undoCount[j]=s->promptDocument.undoCount[i];s->prompt.undoCaret[j]=s->promptDocument.undoCaret[i];memcpy(s->prompt.undo[j],s->promptDocument.undo[i],(size_t)s->promptDocument.undoCount[i]*4);}}
}
static void mirrorIdentity(TextIdentityRun*q,const State*s){
    q->id=s->promptIdentity.id;q->generation=s->promptIdentity.generation;
    if(s->promptIdentity.count<=NR_MAX_TEXT){q->count=s->promptIdentity.count;memcpy(q->source,s->promptIdentity.source,(size_t)q->count*4);memcpy(q->identities,s->promptIdentity.identities,(size_t)q->count*4);}
}
/* The document and identity part of nrPromptStorageMirror, for a direct commit that changed the prompt document,
 * its history or its identity run but no register and no checkpoint (TRANSACTIONS.md, "draft"). It writes the same
 * bytes as the full mirror on a settled State: there the legacy records hold exactly what the previous mirror wrote,
 * so clearing the words that mirror wrote (each record's own count says how many) equals clearing the record. */
void nrPromptMirrorDocument(State*s){
    LegacyPrompt*q=&s->prompt;
    if(q->count>0&&q->count<=(int)NR_MAX_TEXT)memset(q->glyphs,0,(size_t)q->count*4);
    for(int k=0;k<16;k++)if(q->undoCount[k]>0&&q->undoCount[k]<=(int)NR_MAX_TEXT)memset(q->undo[k],0,(size_t)q->undoCount[k]*4);
    memset(&q->count,0,offsetof(LegacyPrompt,undo)-offsetof(LegacyPrompt,count));
    memset(q->undoCount,0,sizeof(*q)-offsetof(LegacyPrompt,undoCount));
    smallPromptFill(&s->promptDocument,q);mirrorRedo(s);
    TextIdentityRun*t=&s->textIdentities[0],*l=&s->legacyTextIdentities[0];
    uint32_t old=t->count<=NR_MAX_TEXT?t->count:0;
    memset(t->source,0,(size_t)old*4);memset(t->identities,0,(size_t)old*4);memset(t,0,offsetof(TextIdentityRun,source));
    mirrorIdentity(t,s);
    uint32_t words=t->count>old?t->count:old;
    memcpy(l,t,offsetof(TextIdentityRun,source));memcpy(l->source,t->source,(size_t)words*4);memcpy(l->identities,t->identities,(size_t)words*4);
}
/* The mirror after a change of the prompt's caret or anchor alone: smallPromptFill copies both from the document
 * header unless the document exceeds the legacy record, when it writes 0 and -1 whatever they are. */
void nrPromptMirrorCaret(State*s){
    if(s->promptDocument.count<=(int)NR_MAX_TEXT){s->prompt.caret=s->promptDocument.caret;s->prompt.anchor=s->promptDocument.anchor;}
}
void nrPromptStorageMirror(State*s){
    memset(s->promptFramed.checkpointText,0,sizeof(s->promptFramed.checkpointText));
    if(s->promptFramed.checkpointCount<=NR_MAX_PROMPT)memcpy(s->promptFramed.checkpointText,s->dynamicPrompt.checkpoint,(size_t)s->promptFramed.checkpointCount*4);
    smallPrompt(&s->promptDocument,&s->prompt);
    mirrorRedo(s);
    memset(&s->vimRegister,0,sizeof(s->vimRegister));
    if(s->promptRegister.count<=(int)NR_MAX_TEXT){memcpy(s->vimRegister.glyphs,s->promptRegister.glyphs,(size_t)s->promptRegister.count*4);s->vimRegister.count=s->promptRegister.count;s->vimRegister.linewise=s->promptRegister.linewise;}
    memset(&s->namedRegisters,0,sizeof(s->namedRegisters));for(int i=0;i<26;i++)if(s->promptRegisters.slots[i].count<=(int)NR_MAX_TEXT){memcpy(s->namedRegisters.slots[i].glyphs,s->promptRegisters.slots[i].glyphs,(size_t)s->promptRegisters.slots[i].count*4);s->namedRegisters.slots[i].count=s->promptRegisters.slots[i].count;s->namedRegisters.slots[i].linewise=s->promptRegisters.slots[i].linewise;}
    memcpy(&s->namedRegisters.pending,&s->promptRegisters.pending,sizeof(s->namedRegisters)-((size_t)((char*)&s->namedRegisters.pending-(char*)&s->namedRegisters)));
    TextIdentityRun*q=&s->textIdentities[0];memset(q,0,sizeof(*q));mirrorIdentity(q,s);
    s->legacyTextIdentities[0]=*q;
}
uint32_t nrPromptLegacyRequired(const State*s,uint32_t schema){
    uint32_t maximum=NR_MAX_TEXT;if(schema>=NR_STATE_SCHEMA_PROMPT_CAPACITY){const PromptFixed70*p=&s->promptFixed70;if(p->count>0&&(uint32_t)p->count>maximum)maximum=p->count;for(int i=0;i<16;i++)if(p->undoCount[i]>0&&(uint32_t)p->undoCount[i]>maximum)maximum=p->undoCount[i];
        if(s->promptRegisterFixed70.count>0&&(uint32_t)s->promptRegisterFixed70.count>maximum)maximum=s->promptRegisterFixed70.count;for(int i=0;i<26;i++)if(s->promptRegistersFixed70.slots[i].count>0&&(uint32_t)s->promptRegistersFixed70.slots[i].count>maximum)maximum=s->promptRegistersFixed70.slots[i].count;}
    if(s->promptFramed.checkpointCount>maximum)maximum=s->promptFramed.checkpointCount;return maximum;
}
static int promoteHistory16(State*s,const uint32_t*text,const int*counts,const int*carets,int head,int size,uint32_t stride){
    Prompt*q=&s->promptDocument;int redo=s->editorRedo.count;if(head<0||head>15||size<0||size>16||redo<0||size+redo>16)return 0;
    for(int i=0;i<16;i++)if(counts[i]<0||counts[i]>(int)stride||carets[i]<0||carets[i]>counts[i])return 0;
    uint64_t total=0;for(int k=0;k<size+redo;k++)total+=(uint32_t)counts[(head-size+k+16)%16];if(!historyRequire(s,total))return 0;
    q->undoHead=size;q->undoSize=size;for(int k=0;k<size+redo;k++){int i=(head-size+k+16)%16;q->undoCount[k]=counts[i];q->undoCaret[k]=carets[i];}
    historyBind(q,q->undo[0]);for(int k=0;k<size+redo;k++){int i=(head-size+k+16)%16;memcpy(q->undo[k],text+(size_t)i*stride,(size_t)counts[i]*4);}return 1;
}
int nrPromptStoragePromote(State*s){
    const LegacyPrompt*p=&s->prompt;if(p->count<0||p->count>(int)NR_MAX_TEXT)return 0;nrPromptRuntimeClear(s);Prompt*q=&s->promptDocument;
    memcpy(&q->count,&p->count,offsetof(Prompt,undo)-offsetof(Prompt,count));memcpy(q->glyphs,p->glyphs,sizeof(p->glyphs));
    q->modal=p->modal;q->revision=p->revision;
    if(!promoteHistory16(s,&p->undo[0][0],p->undoCount,p->undoCaret,p->undoHead,p->undoSize,NR_MAX_TEXT))return 0;
    s->promptRegister.count=s->vimRegister.count;s->promptRegister.linewise=s->vimRegister.linewise;memcpy(s->promptRegister.glyphs,s->vimRegister.glyphs,sizeof(s->vimRegister.glyphs));
    for(int i=0;i<26;i++){s->promptRegisters.slots[i].count=s->namedRegisters.slots[i].count;s->promptRegisters.slots[i].linewise=s->namedRegisters.slots[i].linewise;memcpy(s->promptRegisters.slots[i].glyphs,s->namedRegisters.slots[i].glyphs,sizeof(s->namedRegisters.slots[i].glyphs));}
    s->promptRegisters.pending=s->namedRegisters.pending;s->promptRegisters.selected=s->namedRegisters.selected;s->promptRegisters.append=s->namedRegisters.append;s->promptRegisters.revision=s->namedRegisters.revision;
    const TextIdentityRun*t=&s->textIdentities[0];memcpy(&s->promptIdentity,t,16);memcpy(s->promptIdentity.source,t->source,sizeof(t->source));memcpy(s->promptIdentity.identities,t->identities,sizeof(t->identities));
    memcpy(s->dynamicPrompt.checkpoint,s->promptFramed.checkpointText,(size_t)s->promptFramed.checkpointCount*4);return 1;
}
int nrPromptPromote70(State*s){
    const PromptFixed70*p=&s->promptFixed70;nrPromptRuntimeClear(s);Prompt*q=&s->promptDocument;
    memcpy(&q->count,&p->count,offsetof(Prompt,undo)-offsetof(Prompt,count));q->modal=p->modal;q->revision=p->revision;
    if(p->count<0||p->count>(int)NR_MAX_PROMPT)return 0;memcpy(q->glyphs,p->glyphs,(size_t)p->count*4);
    if(!promoteHistory16(s,&p->undo[0][0],p->undoCount,p->undoCaret,p->undoHead,p->undoSize,NR_MAX_PROMPT))return 0;
    s->promptRegister.count=s->promptRegisterFixed70.count;s->promptRegister.linewise=s->promptRegisterFixed70.linewise;if(s->promptRegister.count<0||s->promptRegister.count>(int)NR_MAX_PROMPT)return 0;memcpy(s->promptRegister.glyphs,s->promptRegisterFixed70.glyphs,(size_t)s->promptRegister.count*4);
    for(int i=0;i<26;i++){PromptRegister*r=&s->promptRegisters.slots[i];r->count=s->promptRegistersFixed70.slots[i].count;r->linewise=s->promptRegistersFixed70.slots[i].linewise;if(r->count<0||r->count>(int)NR_MAX_PROMPT)return 0;memcpy(r->glyphs,s->promptRegistersFixed70.slots[i].glyphs,(size_t)r->count*4);}
    s->promptRegisters.pending=s->promptRegistersFixed70.pending;s->promptRegisters.selected=s->promptRegistersFixed70.selected;s->promptRegisters.append=s->promptRegistersFixed70.append;s->promptRegisters.revision=s->promptRegistersFixed70.revision;
    if(s->promptIdentityFixed70.count>NR_MAX_PROMPT)return 0;memcpy(&s->promptIdentity,&s->promptIdentityFixed70,16);memcpy(s->promptIdentity.source,s->promptIdentityFixed70.source,(size_t)s->promptIdentity.count*4);memcpy(s->promptIdentity.identities,s->promptIdentityFixed70.identities,(size_t)s->promptIdentity.count*4);
    if(s->promptFramed.checkpointCount>NR_MAX_PROMPT)return 0;memcpy(s->dynamicPrompt.checkpoint,s->promptFramed.checkpointText,(size_t)s->promptFramed.checkpointCount*4);return 1;
}
int nrPromptStorageValid(const State*s){
    uint32_t used=s->promptFramed.checkpointCount<=NR_MAX_PROMPT?s->promptFramed.checkpointCount:0;
    if(used&&memcmp(s->promptFramed.checkpointText,s->dynamicPrompt.checkpoint,(size_t)used*4))return 0;
    for(uint32_t i=used;i<NR_MAX_PROMPT;i++)if(s->promptFramed.checkpointText[i])return 0;
    if(s->schema<NR_STATE_SCHEMA_HISTORY100)return 1;LegacyPrompt q;smallPrompt(&s->promptDocument,&q);
    if(s->promptDocument.undoSize+s->editorRedo.count<=16)for(int k=0;k<s->editorRedo.count;k++){int i=(s->promptDocument.undoHead+k)%NR_PROMPT_HISTORY,j=(q.undoHead+k)%16;
        if(s->promptDocument.undoCount[i]<=(int)NR_MAX_TEXT){q.undoCount[j]=s->promptDocument.undoCount[i];q.undoCaret[j]=s->promptDocument.undoCaret[i];memcpy(q.undo[j],s->promptDocument.undo[i],(size_t)s->promptDocument.undoCount[i]*4);}}
    return !memcmp(&q,&s->prompt,sizeof(q));
}
