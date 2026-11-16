/* Command-path bookkeeping (native/docs/TDD-STATE-COPY-ELIMINATION-20261102.md section 5.6; invariants I15, I16).
 * The counters change only at their call sites in nrCommand, nrLoad, nrRender (the render probe sync), nrInit and
 * nrModelSet, through the helpers below; never inside a validator, a pipeline function or a const query. */
#include "internal.h"

/* The cold part of the fixed State prefix (TDD F10): the legacy windows; the trigger, guard and style data formulas
 * with the character rules and regions; legacy text identities 1 to 24; and the legacy window textures through the
 * fixed 70 prompt identity. Every other prefix byte is hot. A whole-prefix copy counts as both. */
#define NR_COLD_PREFIX_BYTES ((uint64_t)sizeof(((State*)0)->legacyWindows) \
    +(uint64_t)(offsetof(State,characterRegions)+sizeof(((State*)0)->characterRegions)-offsetof(State,triggerDataFormulas)) \
    +(uint64_t)(sizeof(((State*)0)->legacyTextIdentities)-sizeof(((State*)0)->legacyTextIdentities[0])) \
    +(uint64_t)(offsetof(State,promptIdentityFixed70)+sizeof(((State*)0)->promptIdentityFixed70)-offsetof(State,legacyWindowTextures)))
#define NR_HOT_PREFIX_BYTES ((uint64_t)offsetof(State,dynamicPrompt)-NR_COLD_PREFIX_BYTES)
_Static_assert(NR_COLD_PREFIX_BYTES==19850800u,"cold prefix bytes of TDD F10");
_Static_assert(NR_HOT_PREFIX_BYTES==10651672u,"hot prefix bytes of TDD F10 plus the 16-byte schema-97 occlusion controls and the 56-byte schema-98 prompt source layer");
_Static_assert(sizeof(NrCommandCounters)==72u,"nine 64-bit work counters");

uint32_t nrCommandPathInitialLimit(void){
    const long long limit=NR_COMMAND_FASTPATH;
    return limit>=0&&limit<=3?(uint32_t)limit:0u;
}
/* One whole-State copy into a context-owned State; a State that no context owns is not counted. */
void nrCountStateCopy(NrContext*c,uint64_t runtimeBytes){
    if(!c)return;
    c->counters.hotBytes+=NR_HOT_PREFIX_BYTES;c->counters.coldBytes+=NR_COLD_PREFIX_BYTES;c->counters.runtimeBytes+=runtimeBytes;
}
/* A full validation at a call site whose condition can stop before nrValidState runs: counted only when it runs. */
int nrCountedValidState(NrContext*c,const State*s){
    c->counters.fullValidations++;
    return nrValidState(s);
}

/* ---------- direct transactions: the bounded record journal (native/docs/TRANSACTIONS.md) ---------- */
/* Record the current bytes of one State record before a direct commit writes it. Returns 0, saving nothing, when
 * the journal is full: the caller then declines before its first write. */
int nrUndoSave(NrContext*c,const void*at,size_t length){
    NrUndo*u=&c->undo;
    if(u->count>=NR_UNDO_RANGES||length>NR_UNDO_BYTES-u->used)return 0;
    NrUndoRange*r=&u->ranges[u->count++];r->at=(unsigned char*)at;r->offset=u->used;r->length=(uint32_t)length;
    memcpy(u->bytes+u->used,at,length);u->used+=(uint32_t)length;u->journaled=1;return 1;
}
/* Put every recorded record back, newest first, and empty the journal. */
void nrUndoRestore(NrContext*c){
    NrUndo*u=&c->undo;
    while(u->count){const NrUndoRange*r=&u->ranges[--u->count];memcpy(r->at,u->bytes+r->offset,r->length);}
    u->used=0;
}

/* ---------- the comparison domain D (TDD section 7 item 5), shared with the verification build ---------- */
static uintptr_t arenaOffset(const void*p,const void*base){return p?(uintptr_t)p-(uintptr_t)base:UINTPTR_MAX;}
static const uint32_t*wireArray(const PromptRuntime*r,unsigned i){
    if(!i)return r->document.glyphs;if(i==101)return r->register0.glyphs;if(i<128)return r->registers.slots[i-102].glyphs;
    if(i==128)return r->identity.source;if(i==129)return r->identity.identities;return r->checkpoint;
}
static int differs(char*where,size_t cap,const char*what,size_t at){
    size_t n=0;if(!cap)return 1;
    while(what[n]&&n+1<cap){where[n]=what[n];n++;}
    if(at!=(size_t)-1&&n+22<cap){char digits[24];int k=0;where[n++]=' ';do{digits[k++]=(char)('0'+at%10);at/=10;}while(at);while(k)where[n++]=digits[--k];}
    where[n]=0;return 1;
}
/* 1 when two States differ anywhere a snapshot, a frame or a later command can observe: the fixed prefix, the
 * prompt runtime's fields (pointers as offsets into each State's own arena), every wire array up to capacity,
 * the used history words, the model records and the modal scalars. */
int nrStateDiffers(const NrContext*c,const State*a,const State*b,char*where,size_t cap){
    const unsigned char*p=(const unsigned char*)a,*q=(const unsigned char*)b;size_t fixed=offsetof(State,dynamicPrompt);
    if(memcmp(p,q,fixed)){size_t i=0;while(p[i]==q[i])i++;return differs(where,cap,"prefix byte",i);}
    const PromptRuntime*r=&a->dynamicPrompt,*s=&b->dynamicPrompt;const Prompt*d=&r->document,*e=&s->document;
    const void*ra=d->glyphs,*rb=e->glyphs;
    if(r->capacity!=s->capacity||r->historyCapacity!=s->historyCapacity||r->scratchWords!=s->scratchWords||(r->owner==c)!=(s->owner==c))return differs(where,cap,"runtime bindings",(size_t)-1);
    if(memcmp(&d->count,&e->count,offsetof(Prompt,undo)-offsetof(Prompt,count))||memcmp(d->undoCount,e->undoCount,sizeof(d->undoCount))||
       memcmp(d->undoCaret,e->undoCaret,sizeof(d->undoCaret))||d->undoHead!=e->undoHead||d->undoSize!=e->undoSize||d->modal!=e->modal||d->revision!=e->revision)
        return differs(where,cap,"prompt document fields",(size_t)-1);
    for(int i=0;i<NR_PROMPT_HISTORY;i++)if(arenaOffset(d->undo[i],ra)!=arenaOffset(e->undo[i],rb))return differs(where,cap,"prompt history binding",(size_t)i);
    if(r->register0.count!=s->register0.count||r->register0.linewise!=s->register0.linewise)return differs(where,cap,"register",(size_t)-1);
    for(int i=0;i<26;i++)if(r->registers.slots[i].count!=s->registers.slots[i].count||r->registers.slots[i].linewise!=s->registers.slots[i].linewise)return differs(where,cap,"named register",(size_t)i);
    if(r->registers.pending!=s->registers.pending||r->registers.selected!=s->registers.selected||r->registers.append!=s->registers.append||r->registers.padding!=s->registers.padding||r->registers.revision!=s->registers.revision)return differs(where,cap,"named register state",(size_t)-1);
    if(r->identity.id!=s->identity.id||r->identity.count!=s->identity.count||r->identity.generation!=s->identity.generation||r->identity.padding!=s->identity.padding)return differs(where,cap,"prompt identity",(size_t)-1);
    for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++){if(i>0&&i<=100)continue;
        const uint32_t*x=wireArray(r,i),*y=wireArray(s,i);
        if(arenaOffset(x,ra)!=arenaOffset(y,rb))return differs(where,cap,"wire array binding",i);
        if(memcmp(x,y,(size_t)r->capacity*4))return differs(where,cap,"wire array",i);
    }
    uint64_t history=0;for(int i=0;i<NR_PROMPT_HISTORY;i++)history+=(uint32_t)d->undoCount[i];
    if(history&&memcmp(d->undo[0],e->undo[0],(size_t)history*4))return differs(where,cap,"history words",(size_t)-1);
    if(a->sourceModel.count&&memcmp(a->modelRecords,b->modelRecords,(size_t)a->sourceModel.count*sizeof(NrModelTriangle)))return differs(where,cap,"model records",(size_t)-1);
    if(a->sourceModal.scalars&&memcmp(a->modalScalars,b->modalScalars,(size_t)a->sourceModal.scalars*4))return differs(where,cap,"modal scalars",(size_t)-1);
    return 0;
}

#if defined(NR_SHADOW_CHECK)&&!defined(__wasm__) /* the verification build is native only */
/* The verification build (native/docs/TRANSACTIONS.md): every command the direct path accepts or rejects is also
 * run through the copy transaction on c->probe, from the same State, and the two outcomes must be identical in
 * return code, error text and D. A journaled op must also not have written any prefix byte outside its journal.
 * A violation prints the command and aborts: test builds only, never shipped. */
#include <stdio.h>
#include <stdlib.h>
static unsigned char*shadowBefore;
/* Per-op tallies, printed at exit: how many commands the direct path committed, rejected and declined. */
static struct {char op[40];unsigned long direct,rejected,invariant,declined;} shadowOps[96];static int shadowOpCount,shadowRegistered;
static void shadowSummary(void){
    for(int i=0;i<shadowOpCount;i++)fprintf(stderr,"NR_SHADOW_CHECK %-24s direct %8lu (accepted %8lu, rejected %6lu, of which State invariant %5lu), declined %8lu\n",shadowOps[i].op,shadowOps[i].direct,shadowOps[i].direct-shadowOps[i].rejected,shadowOps[i].rejected,shadowOps[i].invariant,shadowOps[i].declined);
}
static void shadowTally(const NrContext*c,int result){
    char op[40]={0};int t=nrField(&c->json,0,"op");if(t<0||nrString(&c->json,t,op,sizeof(op))<0)memcpy(op,"(no op)",8);
    int k=0;while(k<shadowOpCount&&strcmp(shadowOps[k].op,op))k++;
    if(k==shadowOpCount){if(shadowOpCount==96)return;memcpy(shadowOps[k].op,op,sizeof(op));shadowOpCount++;}
    if(!shadowRegistered){shadowRegistered=1;atexit(shadowSummary);}
    if(result==NR_DIRECT_DECLINED)shadowOps[k].declined++;
    else{shadowOps[k].direct++;if(result<0){shadowOps[k].rejected++;if(!strcmp(c->error,"State invariant rejected"))shadowOps[k].invariant++;}}
}
static void shadowAbort(const NrContext*c,const char*what,const char*detail){
    fprintf(stderr,"NR_SHADOW_CHECK: %s: %s\n  command: %.*s\n",what,detail,c->json.length>400?400:c->json.length,c->json.text);
    abort();
}
/* A reused pre-render frame must equal a fresh render of the same State. */
static NrCell*shadowCells;static size_t shadowCellCount;
void nrShadowFrame(NrContext*c){
    size_t n=(size_t)c->state.width*c->state.height;
    if(n>shadowCellCount){free(shadowCells);shadowCells=malloc(n*sizeof(NrCell));shadowCellCount=n;if(!shadowCells){fputs("NR_SHADOW_CHECK: out of memory\n",stderr);abort();}}
    memcpy(shadowCells,c->cells,n*sizeof(NrCell));
    if(!nrRender(c))shadowAbort(c,"reused frame","a fresh render failed");
    if(memcmp(shadowCells,c->cells,n*sizeof(NrCell)))shadowAbort(c,"reused frame","a fresh render of the same State differs from the reused frame");
}
int nrShadowDirect(NrContext*c){
    const size_t fixed=offsetof(State,dynamicPrompt);
    if(!shadowBefore&&!(shadowBefore=malloc(fixed))){fputs("NR_SHADOW_CHECK: out of memory\n",stderr);abort();}
    memcpy(shadowBefore,&c->state,fixed);
    nrStateCopy(&c->probe,&c->state);
    int reference=nrCopyTransaction(c,&c->probe);char referenceError[sizeof(c->error)];memcpy(referenceError,c->error,sizeof(c->error));
    c->error[0]=0;
    int result=nrDirectApply(c,&c->json);
    char where[160];
    shadowTally(c,result);
    if(result==NR_DIRECT_DECLINED){
        if(memcmp(shadowBefore,&c->state,fixed))shadowAbort(c,"a declined plan wrote the State","prefix changed");
        c->error[0]=0;return result;
    }
    if(result!=reference||strcmp(c->error,referenceError)){
        char detail[700];snprintf(detail,sizeof(detail),"copy transaction %d \"%s\", direct %d \"%s\"",reference,referenceError,result,c->error);
        shadowAbort(c,"result differs",detail);
    }
    if(nrStateDiffers(c,&c->state,&c->probe,where,sizeof(where)))shadowAbort(c,"State differs from the copy transaction",where);
    if(c->undo.journaled){
        const unsigned char*now=(const unsigned char*)&c->state;
        for(size_t i=0;i<fixed;i++){
            if(!(i&4095)&&i+4096<=fixed&&!memcmp(now+i,shadowBefore+i,4096)){i+=4095;continue;}
            if(now[i]==shadowBefore[i])continue;
            int inside=0;for(uint32_t k=0;k<c->undo.count&&!inside;k++){const NrUndoRange*r=&c->undo.ranges[k];inside=now+i>=r->at&&now+i<r->at+r->length;}
            if(!inside){snprintf(where,sizeof(where),"prefix byte %zu changed outside the journal",i);shadowAbort(c,"undeclared write",where);}
        }
    }
    return result;
}
#endif
