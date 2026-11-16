#include "internal.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint32_t read32(const unsigned char*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static void write32(unsigned char*p,uint32_t n){for(int i=0;i<4;i++)p[i]=(unsigned char)(n>>(8*i));}
static void validWire(const unsigned char*p,uint32_t n){assert(n>=24&&!memcmp(p,"NRRC4SRC",8));assert(read32(p+8)==NR_ABI_VERSION&&read32(p+16)==n-24);assert(read32(p+20)==nrCrc(p+24,n-24));}
static void checksum(unsigned char*p,uint32_t n){assert(n>=24&&read32(p+16)==n-24);write32(p+20,nrCrc(p+24,n-24));validWire(p,n);}
static unsigned char*fixture(const char*name,uint32_t schema,uint32_t payload,uint32_t*n){
 char path[512];int length=snprintf(path,sizeof(path),"tests/fixtures/%s",name);assert(length>0&&(size_t)length<sizeof(path));FILE*f=fopen(path,"rb");
 if(!f){length=snprintf(path,sizeof(path),"native/tests/fixtures/%s",name);assert(length>0&&(size_t)length<sizeof(path));f=fopen(path,"rb");}
 assert(f);assert(fseek(f,0,SEEK_END)==0);long bytes=ftell(f);assert(bytes>=24&&(unsigned long)bytes<=UINT32_MAX);assert(fseek(f,0,SEEK_SET)==0);
 unsigned char*p=malloc((size_t)bytes);assert(p);assert(fread(p,1,(size_t)bytes,f)==(size_t)bytes);assert(fclose(f)==0);*n=(uint32_t)bytes;
 validWire(p,*n);assert(read32(p+12)==schema&&read32(p+16)==payload);return p;
}
static unsigned char*save(NrContext*c,uint32_t*n){*n=nrSnapshotSizeFor(c);assert(*n>=24);unsigned char*p=malloc(*n);assert(p&&nrSave(c,p,*n)==0);validWire(p,*n);return p;}
static void unchanged(NrContext*c,const unsigned char*before,uint32_t n){uint32_t m;unsigned char*after=save(c,&m);assert(n==m&&!memcmp(before,after,n));free(after);}
static void command(NrContext*c,const char*s){int code=nrCommand(c,s,(uint32_t)strlen(s));if(code)fprintf(stderr,"command failed: %s\n%s\n",s,nrError(c));assert(code==0);}
static void*member(unsigned char*p,uint32_t n,size_t offset,size_t bytes){assert(n>=24&&offset<=n-24&&bytes<=n-24-offset);return p+24+offset;}

static void originalSentinel(const char*name,uint32_t schema,int accepted){
 NrContext*c=malloc(nrContextSize());assert(c&&nrInit(c,nrContextSize(),17)==0);
 uint32_t n;unsigned char*input=fixture(name,schema,4414376,&n);assert(nrLoad(c,input,n)==0);
 uint32_t currentSize;unsigned char*before=save(c,&currentSize);int slot=-1;
 for(int i=0;i<NR_TRIGGERS;i++)if(c->state.triggers[i].used){slot=i;break;}assert(slot>=0);
 Trigger*t=member(input,n,offsetof(State,triggers)+slot*sizeof(Trigger),sizeof(Trigger));t->source=NR_TRIGGER_SOURCE_INTENT_VALUE;checksum(input,n);
 int result=nrLoad(c,input,n);if(accepted){assert(result==0&&c->state.triggers[slot].source==NR_TRIGGER_SOURCE_INTENT_VALUE);}else{assert(result<0);unchanged(c,before,currentSize);}
 free(before);free(input);free(c);
}
int main(void){
 originalSentinel("schema-20261002-retained-event-debounce.snapshot",NR_STATE_SCHEMA_OLDEST,0);
 originalSentinel("schema-20261003-retained-intent-selector.snapshot",NR_STATE_SCHEMA_LOCAL_SELECTOR,0);
 originalSentinel("schema-20261004-intent-action.snapshot",NR_STATE_SCHEMA_LOCAL_ACTION,1);
 NrContext*c=malloc(nrContextSize());assert(c&&nrInit(c,nrContextSize(),17)==0);
 command(c,"{\"op\":\"define\",\"path\":\"/source\",\"value\":1}");command(c,"{\"op\":\"define\",\"path\":\"/target\",\"value\":0}");
 command(c,"{\"op\":\"trigger\",\"id\":1,\"source\":\"/source\",\"target\":\"/target\",\"event\":\"/intent/approve\",\"action\":\"set\",\"value\":1}");
 uint32_t n;unsigned char*input=save(c,&n);Trigger*t=member(input,n,offsetof(State,triggers),sizeof(Trigger));assert(t->used);t->source=NR_TRIGGER_SOURCE_INTENT_VALUE;checksum(input,n);
 assert(nrLoad(c,input,n)==0&&c->state.triggers[0].source==NR_TRIGGER_SOURCE_INTENT_VALUE);free(input);free(c);
 puts("PASS: genuine local02/03/04 fixtures load; intent action sentinel rejects atomically in02/03 and succeeds in04/current");return 0;
}
