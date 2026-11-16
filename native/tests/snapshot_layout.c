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

int main(void){
 NrContext*c=malloc(nrContextSize());assert(c&&nrInit(c,nrContextSize(),41)==0);
 uint32_t oldSize;unsigned char*original=fixture("schema-20261003-contracts7-registered-style.snapshot",NR_STATE_SCHEMA_CONTRACTS7,4498608,&oldSize);
 /* Genuine original bytes must load before any adversarial mutation. */
 assert(nrLoad(c,original,oldSize)==0);
 command(c,"{\"op\":\"define\",\"path\":\"/audit/source\",\"value\":7}");
 command(c,"{\"op\":\"define\",\"path\":\"/audit/out\",\"value\":0}");
 command(c,"{\"op\":\"trigger\",\"id\":31,\"event\":\"/review/inspect\",\"when\":{\"path\":\"/audit/source\",\"comparison\":\"at-least\",\"value\":7},\"target\":\"/audit/out\",\"value\":1}");
 int slot=-1;for(int i=0;i<NR_TRIGGERS;i++)if(c->state.triggers[i].used&&c->state.triggers[i].id==31)slot=i;assert(slot>=0);
 unsigned char*control=malloc(oldSize),*input=malloc(oldSize);assert(control&&input);memcpy(control,original,oldSize);
 memcpy(member(control,oldSize,offsetof(State,values),sizeof(c->state.values)),c->state.values,sizeof(c->state.values));
 memcpy(member(control,oldSize,offsetof(State,triggers),sizeof(c->state.triggers)),c->state.triggers,sizeof(c->state.triggers));checksum(control,oldSize);
 assert(nrLoad(c,control,oldSize)==0);uint32_t currentSize;unsigned char*before=save(c,&currentSize),*current=malloc(currentSize);assert(current);
 for(int variant=0;variant<2;variant++){
  memcpy(input,control,oldSize);memcpy(current,before,currentSize);
  Trigger*old=member(input,oldSize,offsetof(State,triggers)+slot*sizeof(Trigger),sizeof(Trigger));
  Trigger*now=member(current,currentSize,offsetof(State,triggers)+slot*sizeof(Trigger),sizeof(Trigger));
  if(variant==0){old->conditions[0].kind=now->conditions[0].kind=4;old->conditions[0].source=now->conditions[0].source=-1;}
  else old->source=now->source=NR_TRIGGER_SOURCE_INTENT_VALUE;
  checksum(current,currentSize);assert(nrLoad(c,current,currentSize)==0);assert(nrLoad(c,before,currentSize)==0);
  checksum(input,oldSize);assert(nrLoad(c,input,oldSize)<0);unchanged(c,before,currentSize);
 }
 free(current);free(before);free(input);free(control);free(original);free(c);
 puts("PASS: genuine Contracts7 fixture and legal control load; intent-value predicate/action accepted by current schema but atomically rejected by exact original schema03 layout");return 0;
}
