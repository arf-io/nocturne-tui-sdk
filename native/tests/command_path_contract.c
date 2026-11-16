/* T2, the command-path contract (native/docs/TDD-STATE-COPY-ELIMINATION-20261102.md sections 5.6, 7, 11.1, 12.1).
 * White-box: includes internal.h and links the shipped dist/libnocturne_native.so (section 11.1's
 * command-path-contract-build command), so Gate A reads the counters of the library that ships.
 *
 *   group 1  Gate A rows A0, A2, A3, A5, A6 and A11 (section 11.1). A0 reads the effective limit of a fresh
 *            context; every other row is asserted in the column that limit selects for it ("column selection").
 *            Compiled out under NR_SHADOW_CHECK, whose counters differ by design; it then prints "not built".
 *   group 2  The two-context differential (section 12.1): a reference context whose limit is cleared to 0,
 *            white-box, before its first command, against a context at the library's default limit. After every
 *            command it compares the return code, nrError and D (section 7, item 5). Corpus: the Tidal Glass load
 *            plus 600 ticks; the four routes of tests/fixtures/scenic-route-ticks.jsonl (load plus 300 gallery
 *            ticks each); every recipe of recipes.json, load plus 100 ticks; every recipe paused, then a time sweep;
 *            scripted direct/full boundary sequences, rejections included; and the T11 gallery streams
 *            tests/fixtures/gallery-stream-*.jsonl when they exist.
 *
 * Usage: command-path-contract [--only <groups> | --except <groups>]   (groups: comma-separated numbers)
 * Every group present in this file runs unless excluded, and prints one line saying whether it ran or was
 * skipped, so a group that lands later needs no qualify edit. qualify runs "--except 2" as the rc2-required
 * command-path-contract-run and "--only 2" as the exhaustive-only command-path-differential.
 * Runs from native/ (qualify's cwd) or from the repository root. */
#include "internal.h"
#include <assert.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CP_GROUPS 2
#define CP_SEED 2030
#define CP_TICK_US 16667u
static unsigned long cpFailures;
static void cpFail(const char*fmt,const char*a,const char*b){
 if(cpFailures++<40){fprintf(stderr,"FAIL ");fprintf(stderr,fmt,a,b);fputc('\n',stderr);}
}

/* ---------- files ---------- */
static char*cpRead(const char*name,size_t*n,int required){
 char path[512];FILE*f=fopen(name,"rb");
 if(!f){int k=snprintf(path,sizeof(path),"native/%s",name);assert(k>0&&(size_t)k<sizeof(path));f=fopen(path,"rb");}
 if(!f){if(required){fprintf(stderr,"missing %s (run from native/ or the repository root)\n",name);exit(1);}return 0;}
 assert(fseek(f,0,SEEK_END)==0);long bytes=ftell(f);assert(bytes>=0&&bytes<(1L<<28));assert(fseek(f,0,SEEK_SET)==0);
 char*p=malloc((size_t)bytes+1);assert(p);assert(fread(p,1,(size_t)bytes,f)==(size_t)bytes);assert(fclose(f)==0);p[bytes]=0;*n=(size_t)bytes;return p;
}
/* recipes.json is indented; whitespace outside strings is dropped, as hosts send compact JSON. */
static size_t cpCompact(const char*s,size_t n,char*out){
 size_t m=0;int string=0,escape=0;
 for(size_t i=0;i<n;i++){char ch=s[i];
  if(string){out[m++]=ch;if(escape)escape=0;else if(ch=='\\')escape=1;else if(ch=='"')string=0;}
  else if(ch=='"'){string=1;out[m++]=ch;}
  else if(ch!=' '&&ch!='\n'&&ch!='\r'&&ch!='\t')out[m++]=ch;
 }
 return m;
}

/* ---------- a context with the storage-growth retries of bindings/python/nocturne_native.py ---------- */
typedef struct {NrContext*c;void*blocks[64];int blockCount;uint64_t commands;} CpContext;
static void cpRelease(CpContext*x){for(int i=0;i<x->blockCount;i++)free(x->blocks[i]);x->blockCount=0;}
static void*cpKeep(CpContext*x,uint64_t bytes){
 assert(x->blockCount<(int)(sizeof(x->blocks)/sizeof(x->blocks[0]))&&bytes&&bytes<=SIZE_MAX-16);
 void*p=calloc(1,(size_t)bytes+16);assert(p);x->blocks[x->blockCount++]=p;return (void*)(((uintptr_t)p+7u)&~(uintptr_t)7u);
}
/* limit: UINT32_MAX keeps the library's default; any other value is stored, white-box, before the first command. */
static void cpOpen(CpContext*x,uint32_t limit){
 cpRelease(x);x->commands=0;
 if(!x->c){x->c=malloc(nrContextSize());assert(x->c);}
 assert(nrInit(x->c,nrContextSize(),CP_SEED)==0);
 if(limit!=UINT32_MAX)x->c->commandPathLimit=limit;
}
static void cpClose(CpContext*x){cpRelease(x);free(x->c);x->c=0;}
static int cpCommand(CpContext*x,const char*text,size_t n){
 int code=nrCommand(x->c,text,(uint32_t)n);x->commands++;
 for(int guard=0;code<0&&guard<16;guard++){
  const char*e=nrError(x->c);uint64_t need;
  if(!strcmp(e,"Prompt storage required")){need=nrPromptMemorySize(x->c);assert(nrSetPromptMemory(x->c,cpKeep(x,need),need)==0);}
  else if(!strcmp(e,"Modal storage required")){need=nrModalMemorySize(x->c);assert(nrSetModalMemory(x->c,cpKeep(x,need),need)==0);}
  else if(!strcmp(e,"Viewport render memory required")){need=nrRenderMemorySize(x->c);assert(nrSetRenderMemory(x->c,cpKeep(x,need),need)==0);}
  else break;
  code=nrCommand(x->c,text,(uint32_t)n);x->commands++;
 }
 return code;
}
static void cpAccept(CpContext*x,const char*text,size_t n){
 int code;do code=cpCommand(x,text,n);while(code==1);
 if(code){fprintf(stderr,"command rejected: %.*s\n%s\n",(int)n,text,nrError(x->c));exit(1);}
}
static void cpAcceptText(CpContext*x,const char*text){cpAccept(x,text,strlen(text));}
static int cpLines(const char*text,size_t n,void(*each)(void*,const char*,size_t),void*arg){
 int lines=0;
 for(const char*line=text;line<text+n;){const char*end=memchr(line,'\n',(size_t)(text+n-line));if(!end)end=text+n;
  if(end>line){each(arg,line,(size_t)(end-line));lines++;}line=end+1;}
 return lines;
}
static void cpAcceptLine(void*arg,const char*line,size_t n){cpAccept(arg,line,n);}
static void cpLoadTidalGlass(CpContext*x){
 size_t n;char*text=cpRead("tests/fixtures/tidal-glass-load.jsonl",&n,1);
 if(cpLines(text,n,cpAcceptLine,x)!=13)cpFail("%s%s","tests/fixtures/tidal-glass-load.jsonl no longer holds the 13-command load","");
 free(text);
}
/* The gallery's scene-art tick for Tidal Glass: ScenicOriginalClock.sample(ms) of
 * bindings/typescript/scenic_original.mjs with the authored rates (water 1, landscape 100 * 0.44704). */
static int cpTidalTick(char*out,size_t cap,uint64_t timeUs,int which){
 if(!which)return snprintf(out,cap,"{\"op\":\"time\",\"timeUs\":%" PRIu64 ",\"budget\":24}",timeUs);
 uint64_t ms=timeUs/1000;double travel=0+(double)ms*(100*.44704)/1000;
 /* JS "% 12000": the corpus stays below 12000 (600 ticks reach about 447), so no libm fmod is linked. */
 assert(travel>=0&&travel<12000);
 return snprintf(out,cap,"{\"op\":\"scene-art\",\"timeMs\":%" PRIu64 ",\"controls\":{\"flow\":1,\"travel\":%.17g}}",ms,travel);
}

/* ---------- group 1: Gate A rows ---------- */
#ifndef NR_SHADOW_CHECK
#define CP_HOT 10651672u /* TDD F10 10,651,600 plus the 16-byte schema-97 occlusion controls and the 56-byte schema-98 prompt source layer */
#define CP_COLD 19850800u
#define CP_COMPARED 4727808u
_Static_assert(offsetof(State,dynamicPrompt)==30502472u,"F10: the fixed State prefix is 30,502,400 bytes plus the 16-byte schema-97 occlusion controls and the 56-byte schema-98 prompt source layer");
typedef struct {uint64_t hot,cold,compared,validations,probes,direct,fallback;} CpExpect;
typedef struct {uint64_t hot,cold,runtime,compared,validations,probes,direct,fallback,audit;} CpDelta;
static CpDelta cpDelta(const NrCommandCounters*a,const NrCommandCounters*b){
 CpDelta d={b->hotBytes-a->hotBytes,b->coldBytes-a->coldBytes,b->runtimeBytes-a->runtimeBytes,b->comparedBytes-a->comparedBytes,
            b->fullValidations-a->fullValidations,b->probeSyncs-a->probeSyncs,b->direct-a->direct,b->fallback-a->fallback,b->auditFaults-a->auditFaults};
 return d;
}
/* A row and its three columns (section 11.1). Today's full path: two whole-prefix copies (each hot 10,651,600 B
 * plus cold 19,850,800 B), the two memcmp gates (characterRules 525,312 B plus characterRegions 4,202,496 B) and
 * one full validation; a render copies nothing. A row takes its flipped value only when the bit it depends on is
 * set in the effective limit. DIRECT (native/docs/TRANSACTIONS.md): pause and a zero-step time are direct commits,
 * which copy, compare and fully validate nothing. A5's SEGMENTS column keeps the stage-1 value (no segment path). */
typedef struct {const char*row,*workload;uint32_t dependsOn;CpExpect stage1,direct,segments;} CpRow;
static const CpRow CP_A2={"A2","pause no-op",NR_PATH_DIRECT,{2u*CP_HOT,2u*CP_COLD,CP_COMPARED,1,0,0,1},{0,0,0,0,0,1,0},{2u*CP_HOT,2u*CP_COLD,CP_COMPARED,1,0,0,1}};
static const CpRow CP_A3={"A3","zero-step time",NR_PATH_DIRECT,{2u*CP_HOT,2u*CP_COLD,CP_COMPARED,1,0,0,1},{0,0,0,0,0,1,0},{2u*CP_HOT,2u*CP_COLD,CP_COMPARED,1,0,0,1}};
static const CpRow CP_A5={"A5","full-path no-op (accessibility, current values)",NR_PATH_SEGMENTS,{2u*CP_HOT,2u*CP_COLD,CP_COMPARED,1,0,0,1},{2u*CP_HOT,2u*CP_COLD,CP_COMPARED,1,0,0,1},{2u*CP_HOT,2u*CP_COLD,CP_COMPARED,1,0,0,1}};
static const CpRow CP_A6={"A6","Tidal Glass render",0,{0,0,0,0,0,0,0},{0,0,0,0,0,0,0},{0,0,0,0,0,0,0}};
static void cpExpect(const char*row,const char*column,uint32_t limit,const CpDelta*d,const CpExpect*e){
 char label[160];snprintf(label,sizeof(label),"%s in the %s column at limit %u",row,column,limit);
 struct {const char*name;uint64_t got,want;} f[]={{"hotBytes",d->hot,e->hot},{"coldBytes",d->cold,e->cold},{"comparedBytes",d->compared,e->compared},
  {"fullValidations",d->validations,e->validations},{"probeSyncs",d->probes,e->probes},{"direct",d->direct,e->direct},{"fallback",d->fallback,e->fallback},{"auditFaults",d->audit,0}};
 for(size_t i=0;i<sizeof(f)/sizeof(f[0]);i++)if(f[i].got!=f[i].want){
  char detail[160];snprintf(detail,sizeof(detail),"%s %" PRIu64 " != %" PRIu64,f[i].name,f[i].got,f[i].want);cpFail("%s: %s",label,detail);
 }
 printf("  %-4s limit %u: asserted in the %s column; copied %" PRIu64 " (hot %" PRIu64 ", cold %" PRIu64 "), runtime %" PRIu64 ", compared %" PRIu64 ", full validations %" PRIu64 ", probe syncs %" PRIu64 ", direct %" PRIu64 ", fallback %" PRIu64 "\n",
  row,limit,column,d->hot+d->cold,d->hot,d->cold,d->runtime,d->compared,d->validations,d->probes,d->direct,d->fallback);
}
static const char*cpColumn(const CpRow*r,uint32_t limit,const CpExpect**e){
 if(r->dependsOn&&(limit&r->dependsOn)){*e=r->dependsOn==NR_PATH_DIRECT?&r->direct:&r->segments;return r->dependsOn==NR_PATH_DIRECT?"DIRECT":"SEGMENTS";}
 *e=&r->stage1;return "stage-1";
}
static CpDelta cpMeasure(CpContext*x,const char*text,int*code){
 NrCommandCounters before=x->c->counters;*code=cpCommand(x,text,strlen(text));return cpDelta(&before,&x->c->counters);
}
static void cpRowCommand(CpContext*x,const CpRow*r,const char*text,uint32_t limit,int forceStage1){
 int code;CpDelta d=cpMeasure(x,text,&code);
 if(code!=0)cpFail("%s: command rejected: %s",r->row,nrError(x->c));
 const CpExpect*e;const char*column=forceStage1?(e=&r->stage1,"limit-0 (today's)"):cpColumn(r,limit,&e);
 char row[48];snprintf(row,sizeof(row),forceStage1?"A11/%s":"%s",r->row);cpExpect(row,column,limit,&d,e);
}
static void cpRows(CpContext*x,uint32_t limit,int limitZeroRow){
 char text[160];State*s=&x->c->state;int paused=s->paused,step=(int)s->step;
 cpRowCommand(x,&CP_A2,"{\"op\":\"pause\"}",limit,limitZeroRow);
 if(s->paused!=paused)cpFail("%s%s","A2: the no-op pause changed paused","");
 snprintf(text,sizeof(text),"{\"op\":\"time\",\"timeUs\":%" PRIu64 "}",(uint64_t)s->timeUs);
 cpRowCommand(x,&CP_A3,text,limit,limitZeroRow);
 if((int)s->step!=step)cpFail("%s%s","A3: the zero-step time advanced the step","");
 cpRowCommand(x,&CP_A5,"{\"op\":\"accessibility\",\"reducedMotion\":false,\"screenReader\":false}",limit,limitZeroRow);
 NrCommandCounters before=x->c->counters;uint32_t cells=nrRender(x->c);CpDelta d=cpDelta(&before,&x->c->counters);
 if(cells!=160u*52u)cpFail("%s: render returned %s cells","A6",cells?"a wrong number of":"no");
 const CpExpect*e;const char*column=limitZeroRow?(e=&CP_A6.stage1,"limit-0 (today's)"):cpColumn(&CP_A6,limit,&e);
 cpExpect(limitZeroRow?"A11/A6":"A6",column,limit,&d,e);
}
static void cpGroup1(void){
 CpContext x={0};cpOpen(&x,UINT32_MAX);
 const NrCommandCounters zero={0};uint32_t limit=x.c->commandPathLimit;
 printf("  A0   fresh context of the linked library: commandPathLimit %u; this test compiled NR_COMMAND_FASTPATH %d from internal.h\n",limit,(int)NR_COMMAND_FASTPATH);
 if(limit!=(uint32_t)NR_COMMAND_FASTPATH)cpFail("%s%s","A0: the library's effective limit differs from the internal.h default this test compiled (a stray NOCTURNE_COMMAND_FASTPATH build?)","");
 if(memcmp(&x.c->counters,&zero,sizeof(zero)))cpFail("%s%s","A0: a fresh context's counters are not zero","");
 cpLoadTidalGlass(&x);cpRows(&x,limit,0);
 /* A11: today's numbers exactly, on a context whose limit is cleared before its first command. */
 cpOpen(&x,0);if(x.c->commandPathLimit!=0)cpFail("%s%s","A11: the limit did not clear","");
 cpLoadTidalGlass(&x);cpRows(&x,0,1);
 cpClose(&x);
}
#endif

/* ---------- group 2: two-context differential over D ---------- */
static uintptr_t cpOffset(const void*p,const void*base){return p?(uintptr_t)p-(uintptr_t)base:UINTPTR_MAX;}
typedef struct {unsigned char*bytes;size_t used,cap;} CpBuf;
static void cpPut(CpBuf*b,const void*p,size_t n){
 if(b->used+n>b->cap){b->cap=(b->used+n)*2+1024;b->bytes=realloc(b->bytes,b->cap);assert(b->bytes);}
 memcpy(b->bytes+b->used,p,n);b->used+=n;
}
#define CP_PUT(b,field) cpPut(b,&(field),sizeof(field))
static void cpPutOffset(CpBuf*b,const void*p,const void*base){uint64_t v=(uint64_t)cpOffset(p,base);CP_PUT(b,v);}
/* D (b): the non-pointer fields of dynamicPrompt, its pointers as offsets from the State's own arena base. */
static void cpRuntimeImage(const NrContext*c,const State*s,CpBuf*b){
 const PromptRuntime*r=&s->dynamicPrompt;const void*base=r->document.glyphs;const Prompt*d=&r->document;
 cpPutOffset(b,d->glyphs,base);
 CP_PUT(b,d->count);CP_PUT(b,d->caret);CP_PUT(b,d->anchor);CP_PUT(b,d->mode);CP_PUT(b,d->active);CP_PUT(b,d->minRows);CP_PUT(b,d->maxRows);
 CP_PUT(b,d->border);CP_PUT(b,d->padding);CP_PUT(b,d->vimMode);CP_PUT(b,d->alpha);
 for(int i=0;i<NR_PROMPT_HISTORY;i++)cpPutOffset(b,d->undo[i],base);
 CP_PUT(b,d->undoCount);CP_PUT(b,d->undoCaret);CP_PUT(b,d->undoHead);CP_PUT(b,d->undoSize);CP_PUT(b,d->modal);CP_PUT(b,d->revision);
 cpPutOffset(b,r->register0.glyphs,base);CP_PUT(b,r->register0.count);CP_PUT(b,r->register0.linewise);
 for(int i=0;i<26;i++){cpPutOffset(b,r->registers.slots[i].glyphs,base);CP_PUT(b,r->registers.slots[i].count);CP_PUT(b,r->registers.slots[i].linewise);}
 CP_PUT(b,r->registers.pending);CP_PUT(b,r->registers.selected);CP_PUT(b,r->registers.append);CP_PUT(b,r->registers.padding);CP_PUT(b,r->registers.revision);
 CP_PUT(b,r->identity.id);CP_PUT(b,r->identity.count);CP_PUT(b,r->identity.generation);CP_PUT(b,r->identity.padding);
 cpPutOffset(b,r->identity.source,base);cpPutOffset(b,r->identity.identities,base);
 cpPutOffset(b,r->checkpoint,base);cpPutOffset(b,r->scratch,base);
 CP_PUT(b,r->capacity);CP_PUT(b,r->scratchWords);CP_PUT(b,r->historyCapacity);
 unsigned char own=r->owner==c;CP_PUT(b,own);
}
static const uint32_t*cpDataArray(const PromptRuntime*r,unsigned i){
 if(!i)return r->document.glyphs;if(i==101)return r->register0.glyphs;if(i<128)return r->registers.slots[i-102].glyphs;
 if(i==128)return r->identity.source;if(i==129)return r->identity.identities;return r->checkpoint;
}
/* The comparison domain D of section 7, item 5, parts (a) to (f). Returns 1 and names the first difference. */
static int cpDifferent(const NrContext*a,const NrContext*b,char*where,size_t cap){
 const State*s=&a->state,*t=&b->state;const size_t fixed=offsetof(State,dynamicPrompt);
 const unsigned char*p=(const unsigned char*)s,*q=(const unsigned char*)t;
 if(memcmp(p,q,fixed)){size_t i=0;while(p[i]==q[i])i++;snprintf(where,cap,"D(a) prefix byte %zu",i);return 1;}
 static CpBuf x,y;x.used=y.used=0;cpRuntimeImage(a,s,&x);cpRuntimeImage(b,t,&y);
 if(x.used!=y.used||memcmp(x.bytes,y.bytes,x.used)){size_t i=0;while(i<x.used&&i<y.used&&x.bytes[i]==y.bytes[i])i++;snprintf(where,cap,"D(b) dynamicPrompt image byte %zu",i);return 1;}
 const PromptRuntime*r=&s->dynamicPrompt,*u=&t->dynamicPrompt;uint32_t words=r->capacity;
 for(unsigned i=0;i<NR_PROMPT_WIRE_ARRAYS;i++){if(i>0&&i<=100)continue;
  if(memcmp(cpDataArray(r,i),cpDataArray(u,i),(size_t)words*4)){snprintf(where,cap,"D(c) data array %u",i);return 1;}}
 uint64_t history=0;for(int i=0;i<NR_PROMPT_HISTORY;i++)history+=(uint32_t)r->document.undoCount[i];
 if(history&&memcmp(r->document.undo[0],u->document.undo[0],(size_t)history*4)){snprintf(where,cap,"D(d) history words");return 1;}
 if(s->sourceModel.count&&memcmp(s->modelRecords,t->modelRecords,(size_t)s->sourceModel.count*sizeof(NrModelTriangle))){snprintf(where,cap,"D(e) model records");return 1;}
 if(s->sourceModal.scalars&&memcmp(s->modalScalars,t->modalScalars,(size_t)s->sourceModal.scalars*4)){snprintf(where,cap,"D(f) modal scalars");return 1;}
 return 0;
}
typedef struct {CpContext ref,cand;const char*item;unsigned long commands,differences,rejected,items;uint64_t candDirect,candFallback;} CpPair;
static void cpPairOpen(CpPair*p,const char*item){
 cpOpen(&p->ref,0);cpOpen(&p->cand,UINT32_MAX);p->item=item;p->items++;
 if(p->ref.c->commandPathLimit!=0)cpFail("%s: %s",item,"the reference context's limit did not clear");
}
static int cpPairSend(CpPair*p,const char*text,size_t n){
 uint64_t direct=p->cand.c->counters.direct,fallback=p->cand.c->counters.fallback;
 int a=cpCommand(&p->ref,text,n),b=cpCommand(&p->cand,text,n);p->commands++;
 p->candDirect+=p->cand.c->counters.direct-direct;p->candFallback+=p->cand.c->counters.fallback-fallback;
 char where[96];
 if(a!=b||strcmp(nrError(p->ref.c),nrError(p->cand.c))){
  p->differences++;char detail[600];snprintf(detail,sizeof(detail),"%.*s: reference %d \"%s\", candidate %d \"%s\"",(int)(n>200?200:n),text,a,nrError(p->ref.c),b,nrError(p->cand.c));
  cpFail("group 2 %s: result differs at %s",p->item,detail);
 }else if(cpDifferent(p->ref.c,p->cand.c,where,sizeof(where))){
  p->differences++;char detail[400];snprintf(detail,sizeof(detail),"%s after %.*s",where,(int)(n>200?200:n),text);
  cpFail("group 2 %s: D differs: %s",p->item,detail);
 }
 if(a<0)p->rejected++;
 return a;
}
static int cpPairText(CpPair*p,const char*text){return cpPairSend(p,text,strlen(text));}
static void cpPairAccept(CpPair*p,const char*text,size_t n){
 int code;do code=cpPairSend(p,text,n);while(code==1);
 if(code){char detail[300];snprintf(detail,sizeof(detail),"%.*s: %s",(int)(n>200?200:n),text,nrError(p->ref.c));cpFail("group 2 %s: load command rejected: %s",p->item,detail);}
}
static void cpPairAcceptLine(void*arg,const char*line,size_t n){cpPairAccept(arg,line,n);}
static void cpPairTicks(CpPair*p,uint64_t startUs,int ticks,int sceneArt){
 char text[256];
 for(int k=1;k<=ticks;k++){uint64_t at=startUs+(uint64_t)k*CP_TICK_US;
  int n=cpTidalTick(text,sizeof(text),at,0);assert(n>0&&(size_t)n<sizeof(text));cpPairSend(p,text,(size_t)n);
  if(sceneArt){n=cpTidalTick(text,sizeof(text),at,1);assert(n>0&&(size_t)n<sizeof(text));cpPairSend(p,text,(size_t)n);}
 }
}
static void cpPrintItem(const CpPair*p,unsigned long before,unsigned long diffBefore){
 printf("  %-34s %6lu commands, %lu differences\n",p->item,p->commands-before,p->differences-diffBefore);
}
/* The fixture's route blocks: a {"route":...} header, then the route's load commands and its ticks. */
typedef struct {CpPair*p;char name[96];unsigned long before,diffBefore;int routes;} CpRoutes;
static void cpRouteLine(void*arg,const char*line,size_t n){
 CpRoutes*r=arg;
 if(n>9&&!memcmp(line,"{\"route\":",9)){
  if(r->routes)cpPrintItem(r->p,r->before,r->diffBefore);
  const char*name=line+10;size_t k=0;while(name+k<line+n&&name[k]!='"'&&k+1<sizeof(r->name)-8)k++;
  snprintf(r->name,sizeof(r->name),"route %.*s",(int)k,name);cpPairOpen(r->p,r->name);r->before=r->p->commands;r->diffBefore=r->p->differences;r->routes++;return;
 }
 if(!r->routes){cpFail("%s%s","scenic-route-ticks.jsonl: a command precedes the first route header","");return;}
 if(cpPairSend(r->p,line,n)<0){char detail[300];snprintf(detail,sizeof(detail),"%.*s: %s",(int)(n>200?200:n),line,nrError(r->p->ref.c));cpFail("%s: fixture command rejected: %s",r->name,detail);}
}
/* A T11 stream: {"frame":...} markers, and every other line is the exact text NativeScene.command sent,
 * from the page's load on (native/scripts/capture_gallery_stream.py). */
static void cpStreamLine(void*arg,const char*line,size_t n){
 CpPair*p=arg;if(n>8&&!memcmp(line,"{\"frame\"",8))return;
 cpPairSend(p,line,n);
}
static const char*CP_BOUNDARY[]={
 "{\"op\":\"pause\"}","{\"op\":\"time\",\"timeUs\":@0}","{\"op\":\"time\",\"timeUs\":@16667,\"budget\":24}","{\"op\":\"scene-art\",\"timeMs\":#,\"controls\":{\"flow\":1,\"travel\":1.5}}",
 "{\"op\":\"accessibility\",\"reducedMotion\":false,\"screenReader\":false}","{\"op\":\"time\",\"timeUs\":@33334,\"budget\":24}",
 "{\"op\":\"scene-art\",\"timeMs\":null,\"controls\":{\"flow\":1,\"travel\":2}}","{\"op\":\"scene-art\",\"controls\":{\"flow\":0}}",
 "{\"op\":\"scene-art\",\"controls\":{\"yaw\":36}}","{\"op\":\"time\",\"timeUs\":@16667,\"budget\":24}",
 "{\"op\":\"resize\",\"width\":160,\"height\":52}","{\"op\":\"time\",\"timeUs\":@8333}","{\"op\":\"time\",\"timeUs\":@8334}",
 "{\"op\":\"pause\",\"paused\":true}","{\"op\":\"time\",\"timeUs\":@1000000}","{\"op\":\"scene-art\",\"timeMs\":#,\"controls\":{\"flow\":1,\"travel\":3}}",
 "{\"op\":\"pause\",\"paused\":true}","{\"op\":\"time\",\"timeUs\":@0}","{\"op\":\"pause\",\"paused\":false}","{\"op\":\"time\",\"timeUs\":@16666,\"budget\":24}",
 "{\"op\":\"time\",\"timeUs\":@1000000,\"budget\":1}","{\"op\":\"time\",\"timeUs\":@0,\"budget\":24}","{\"op\":\"time\",\"timeUs\":@1000000}",
 "{\"op\":\"time\",\"timeUs\":0}","{\"op\":\"time\",\"timeUs\":@16667,\"budget\":0}","{\"op\":\"time\",\"timeUs\":@16667,\"step\":1}",
 "{\"op\":\"scene-art\",\"timeMs\":-1}","{\"op\":\"scene-art\",\"timeMs\":1.5}","{\"op\":\"scene-art\",\"controls\":{\"unknown\":1}}",
 "{\"op\":\"pause\",\"paused\":2}","{\"op\":\"time\",\"timeUs\":@16667,\"budget\":24}","{\"op\":\"scene-art\",\"timeMs\":#,\"controls\":{\"flow\":1,\"travel\":4}}",
 "{\"op\":\"remove-scene-art\"}","{\"op\":\"time\",\"timeUs\":@16667,\"budget\":24}","{\"op\":\"pause\"}",
};
/* "@d" is the reference context's current timeUs plus d; "#" is its current time in whole milliseconds. */
static void cpBoundary(CpPair*p){
 char text[256];
 for(size_t k=0;k<sizeof(CP_BOUNDARY)/sizeof(CP_BOUNDARY[0]);k++){
  const char*f=CP_BOUNDARY[k];size_t m=0;
  for(const char*c=f;*c&&m+40<sizeof(text);c++){
   if(*c=='@'){char*end;unsigned long long d=strtoull(c+1,&end,10);m+=(size_t)snprintf(text+m,sizeof(text)-m,"%" PRIu64,(uint64_t)p->ref.c->state.timeUs+d);c=end-1;}
   else if(*c=='#')m+=(size_t)snprintf(text+m,sizeof(text)-m,"%" PRIu64,(uint64_t)p->ref.c->state.timeUs/1000);
   else text[m++]=*c;
  }
  text[m]=0;cpPairText(p,text);
 }
}
static Json cpRecipes;
static void cpGroup2(void){
 CpPair p;memset(&p,0,sizeof(p));unsigned long before,diffBefore;char text[256];
 /* Tidal Glass load plus 600 ticks: time +2 steps (budget 24), then the gallery's scene-art. */
 cpPairOpen(&p,"tidal-glass load + 600 ticks");before=p.commands;diffBefore=p.differences;
 {size_t n;char*t=cpRead("tests/fixtures/tidal-glass-load.jsonl",&n,1);if(cpLines(t,n,cpPairAcceptLine,&p)!=13)cpFail("%s%s","tidal-glass-load.jsonl no longer holds 13 commands","");free(t);}
 cpPairTicks(&p,p.ref.c->state.timeUs,600,1);cpPrintItem(&p,before,diffBefore);
 /* Scripted direct/full boundaries on the Tidal Glass state, rejections included. */
 cpPairOpen(&p,"tidal-glass boundary sequences");before=p.commands;diffBefore=p.differences;
 {size_t n;char*t=cpRead("tests/fixtures/tidal-glass-load.jsonl",&n,1);cpLines(t,n,cpPairAcceptLine,&p);free(t);}
 cpBoundary(&p);cpPairTicks(&p,p.ref.c->state.timeUs,4,1);cpBoundary(&p);cpPrintItem(&p,before,diffBefore);
 /* The four scenic routes, each its load plus 300 gallery ticks, as the gallery's own clock samples them. */
 {size_t n;char*t=cpRead("tests/fixtures/scenic-route-ticks.jsonl",&n,1);CpRoutes r={&p,{0},0,0,0};cpLines(t,n,cpRouteLine,&r);
  if(r.routes)cpPrintItem(&p,r.before,r.diffBefore);if(r.routes!=4)cpFail("%s%s","scenic-route-ticks.jsonl does not hold the four routes","");free(t);}
 /* Every recipe: its load plus 100 ticks; then paused, a time sweep that changes nothing. */
 size_t n;char*file=cpRead("recipes.json",&n,1),*wrapped=malloc(n+8),*command=malloc(n+1);assert(wrapped&&command);
 memcpy(wrapped,"{\"r\":",5);memcpy(wrapped+5,file,n);wrapped[n+5]='}';wrapped[n+6]=0;
 if(!nrParse(&cpRecipes,wrapped,(int)n+6)){fprintf(stderr,"recipes.json: %s\n",cpRecipes.error);exit(1);}
 int list=nrField(&cpRecipes,0,"r"),count=0;assert(list>=0&&cpRecipes.tokens[list].type==J_ARRAY);
 static const uint64_t sweep[]={0,1,8333,8334,16666,16667,1000000};
 for(int paused=0;paused<2;paused++)for(int r=list+1;r<cpRecipes.tokens[list].next;r=cpRecipes.tokens[r].next){
  char id[96],item[160];int at=nrField(&cpRecipes,r,"id"),commands=nrField(&cpRecipes,r,"commands");
  assert(at>=0&&nrString(&cpRecipes,at,id,sizeof(id))>=0&&commands>=0&&cpRecipes.tokens[commands].type==J_ARRAY);
  snprintf(item,sizeof(item),paused?"recipe %s, paused sweep":"recipe %s + 100 ticks",id);
  cpPairOpen(&p,item);before=p.commands;diffBefore=p.differences;
  static const char reset[]="{\"op\":\"reset\",\"seed\":2030}";cpPairAccept(&p,reset,sizeof(reset)-1);
  for(int k=commands+1;k<cpRecipes.tokens[commands].next;k=cpRecipes.tokens[k].next){
   const JToken*t=&cpRecipes.tokens[k];cpPairAccept(&p,command,cpCompact(wrapped+t->start,(size_t)(t->end-t->start),command));
  }
  if(!paused){cpPairText(&p,"{\"op\":\"pause\",\"paused\":false}");cpPairTicks(&p,p.ref.c->state.timeUs,100,0);count++;}
  else{
   cpPairText(&p,"{\"op\":\"pause\",\"paused\":true}");uint64_t base=p.ref.c->state.timeUs;
   for(size_t k=0;k<sizeof(sweep)/sizeof(sweep[0]);k++){snprintf(text,sizeof(text),"{\"op\":\"time\",\"timeUs\":%" PRIu64 ",\"budget\":24}",base+sweep[k]);cpPairText(&p,text);}
   cpPairText(&p,"{\"op\":\"time\",\"timeUs\":86400000000}");cpPairText(&p,"{\"op\":\"time\"}");
   cpPairText(&p,"{\"op\":\"pause\",\"paused\":false}");cpPairTicks(&p,p.ref.c->state.timeUs,2,0);
  }
  cpPrintItem(&p,before,diffBefore);
 }
 if(count!=30)cpFail("%s%s","recipes.json no longer holds 30 recipes; review this test's corpus","");
 free(command);free(wrapped);free(file);
 /* The T11 captured gallery streams (step 1.9), when they exist. */
 static const char*streams[]={"tests/fixtures/gallery-stream-tidal-glass.jsonl","tests/fixtures/gallery-stream-tidal-glass-modal.jsonl"};
 for(size_t k=0;k<sizeof(streams)/sizeof(streams[0]);k++){
  size_t m;char*t=cpRead(streams[k],&m,0);
  if(!t){printf("  %-34s absent (captured at step 1.9)\n",streams[k]+15);continue;}
  cpPairOpen(&p,streams[k]+15);before=p.commands;diffBefore=p.differences;cpLines(t,m,cpStreamLine,&p);cpPrintItem(&p,before,diffBefore);free(t);
 }
 printf("  group 2: %lu corpus items, %lu commands compared (%lu rejected in both), %lu differences; candidate direct %" PRIu64 ", fallback %" PRIu64 "; reference limit 0, candidate limit %u\n",
  p.items,p.commands,p.rejected,p.differences,p.candDirect,p.candFallback,p.cand.c->commandPathLimit);
 if(!p.commands)cpFail("%s%s","group 2 compared no command","");
 cpClose(&p.ref);cpClose(&p.cand);
}

/* ---------- groups ---------- */
static int cpListed(const char*list,int group){
 for(const char*c=list;*c;){char*end;long v=strtol(c,&end,10);if(end==c){fprintf(stderr,"bad group list: %s\n",list);exit(2);}if(v==group)return 1;c=*end==','?end+1:end;if(*end&&*end!=','){fprintf(stderr,"bad group list: %s\n",list);exit(2);}}
 return 0;
}
int main(int argc,char**argv){
 const char*only=0,*except=0;
 for(int i=1;i<argc;i++){
  if(!strcmp(argv[i],"--only")&&i+1<argc&&!only&&!except)only=argv[++i];
  else if(!strcmp(argv[i],"--except")&&i+1<argc&&!only&&!except)except=argv[++i];
  else{fprintf(stderr,"usage: %s [--only <groups> | --except <groups>]\n",argv[0]);return 2;}
 }
 printf("command-path contract: context %u bytes, NR_COMMAND_FASTPATH %d as compiled here\n",nrContextSize(),(int)NR_COMMAND_FASTPATH);
 for(int g=1;g<=CP_GROUPS;g++){
  if((only&&!cpListed(only,g))||(except&&cpListed(except,g))){printf("group %d: skipped (%s)\n",g,only?"--only":"--except");continue;}
  unsigned long before=cpFailures;
  switch(g){
#ifndef NR_SHADOW_CHECK
   case 1:printf("group 1: Gate A rows\n");cpGroup1();break;
#else
   case 1:printf("group 1: not built (NR_SHADOW_CHECK)\n");continue;
#endif
   case 2:printf("group 2: two-context differential, limit 0 against the default\n");cpGroup2();break;
  }
  printf("group %d: %s\n",g,cpFailures==before?"PASS":"FAIL");
 }
 if(cpFailures){fprintf(stderr,"FAIL: %lu command-path contract failures\n",cpFailures);return 1;}
 puts("PASS: command-path contract");
 return 0;
}
