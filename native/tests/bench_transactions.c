/* Per-op transaction cost (native/docs/TRANSACTIONS.md, "Measurement").
 *
 * White-box: compiled together with the core sources and -DNR_BENCH_HOOKS. It replays a stream (default: the three
 * composite screens at 160x48), warms each entry for N frames, then times every later command. Per op it prints
 * medians and 99th percentiles of
 *   total   nrCommand wall time (the pointer/wheel pre-render included)
 *   body    the op's own work: for a direct command the wall time inside its plan and commit (NR_BENCH_HOOKS);
 *           in --copy mode nrTransaction on a fresh trial copy (the copy itself not timed)
 *   over    total minus body: the transaction overhead
 * and the work counters per command (whole-State bytes copied, full validations).
 * Usage: bench-transactions [--copy] [--warm N] [stream.jsonl]   (default stream: the composite stream). --copy clears
 * commandPathLimit (the copy transaction for every command); the default is NR_PATH_DIRECT. Run the two modes as
 * separate processes so neither one's 30 MB copies evict the other's working set. */
#include "internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e3+t.tv_nsec/1e6;}
typedef struct {NrContext*c;void*blocks[64];int n;} Ctx;
static void*keep(Ctx*x,uint64_t bytes){void*p=calloc(1,(size_t)bytes+16);x->blocks[x->n++]=p;return (void*)(((uintptr_t)p+7u)&~(uintptr_t)7u);}
static void ctxOpen(Ctx*x,uint32_t limit){
    for(int i=0;i<x->n;i++)free(x->blocks[i]);x->n=0;
    if(!x->c)x->c=malloc(nrContextSize());
    nrInit(x->c,nrContextSize(),2030);x->c->commandPathLimit=limit;
}
static int send(Ctx*x,const char*t,size_t n){
    int code=nrCommand(x->c,t,(uint32_t)n);
    for(int g=0;code<0&&g<16;g++){const char*e=nrError(x->c);uint64_t need;
        if(!strcmp(e,"Prompt storage required")){need=nrPromptMemorySize(x->c);nrSetPromptMemory(x->c,keep(x,need),need);}
        else if(!strcmp(e,"Modal storage required")){need=nrModalMemorySize(x->c);nrSetModalMemory(x->c,keep(x,need),need);}
        else if(!strcmp(e,"Viewport render memory required")){need=nrRenderMemorySize(x->c);nrSetRenderMemory(x->c,keep(x,need),need);}
        else break;
        code=nrCommand(x->c,t,(uint32_t)n);}
    return code;
}
#define MAXS 200000
typedef struct {char op[32];double direct[4096],body[4096];int n;uint64_t copied,validations,directCount;} Op;
static Op ops[64];static int opCount;
static Op*opFor(const char*line){
    char op[32]="?";const char*p=strstr(line,"\"op\":\"");if(p){p+=6;int k=0;while(p[k]&&p[k]!='"'&&k<31){op[k]=p[k];k++;}op[k]=0;}
    for(int i=0;i<opCount;i++)if(!strcmp(ops[i].op,op))return &ops[i];
    if(opCount==64)return 0;memcpy(ops[opCount].op,op,32);return &ops[opCount++];
}
static int cmpd(const void*a,const void*b){double x=*(const double*)a,y=*(const double*)b;return x<y?-1:x>y;}
static double pct(double*v,int n,double p){if(!n)return 0;double*w=malloc(sizeof(double)*(size_t)n);memcpy(w,v,sizeof(double)*(size_t)n);qsort(w,(size_t)n,sizeof(double),cmpd);double r=w[(int)(p*(n-1))];free(w);return r;}
int main(int argc,char**argv){
    const char*path="tests/fixtures/transactions/streams/composite.jsonl";int warm=120;uint32_t limit=NR_PATH_DIRECT;
    for(int i=1;i<argc;i++){if(!strcmp(argv[i],"--warm")&&i+1<argc)warm=atoi(argv[++i]);else if(!strcmp(argv[i],"--copy"))limit=0;else path=argv[i];}
    FILE*f=fopen(path,"rb");if(!f){fprintf(stderr,"cannot open %s\n",path);return 2;}
    static Ctx a;static char line[1<<20];int frame=0,opened=0;
    printf("mode: %s (commandPathLimit %u), stream %s, %d warm frames per entry\n",limit?"direct":"copy transaction",limit,path,warm);
    while(fgets(line,sizeof(line),f)){
        size_t n=strlen(line);while(n&&(line[n-1]=='\n'||line[n-1]=='\r'))line[--n]=0;if(!n)continue;
        if(!strncmp(line,"{\"entry\":",9)){ctxOpen(&a,limit);frame=0;opened=1;continue;}
        if(!opened)continue;
        int tick=!strncmp(line,"{\"op\":\"time\"",12);if(tick)frame++;
        if(frame<=warm){int r;do r=send(&a,line,n);while(r==1);if(tick)nrRender(a.c);continue;}
        Op*o=opFor(line);double body=0;
        if(!limit){ /* the copy transaction's handler body: nrTransaction on a fresh trial copy (copy not timed) */
            nrStateCopy(&a.c->trial,&a.c->state);nrParse(&a.c->json,line,(int)n);
            double t0=now();nrTransaction(a.c,&a.c->trial,&a.c->json);body=now()-t0;a.c->error[0]=0;
        }
        NrCommandCounters before=a.c->counters;a.c->benchBodyMs=0;
        double t0=now();send(&a,line,n);double t1=now();
        if(a.c->counters.direct!=before.direct)body=a.c->benchBodyMs;
        if(o&&o->n<4096){o->direct[o->n]=t1-t0;o->body[o->n]=body;o->n++;
            o->copied+=(a.c->counters.hotBytes-before.hotBytes)+(a.c->counters.coldBytes-before.coldBytes);
            o->validations+=a.c->counters.fullValidations-before.fullValidations;o->directCount+=a.c->counters.direct-before.direct;}
        if(tick)nrRender(a.c);
    }
    printf("%-14s %6s %8s | %9s %9s | %9s %9s | %9s %9s | %12s %6s\n","op","n","direct%","total p50","p99","body p50","p99","over p50","p99","bytes/cmd","valid");
    for(int i=0;i<opCount;i++){Op*o=&ops[i];double over[4096];for(int k=0;k<o->n;k++)over[k]=o->direct[k]-o->body[k];
        printf("%-14s %6d %7.1f%% | %9.4f %9.4f | %9.4f %9.4f | %9.4f %9.4f | %12.0f %6.2f\n",o->op,o->n,o->n?100.0*o->directCount/o->n:0,
            pct(o->direct,o->n,.5),pct(o->direct,o->n,.99),pct(o->body,o->n,.5),pct(o->body,o->n,.99),pct(over,o->n,.5),pct(over,o->n,.99),
            o->n?(double)o->copied/o->n:0,o->n?(double)o->validations/o->n:0);}
    return 0;
}
