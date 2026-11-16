/* Actual public ABI storage, payload and ownership boundaries. */
#include "internal.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static uint8_t *save(NrContext*c,uint32_t*n){*n=nrSnapshotSizeFor(c);uint8_t*p=malloc(*n);assert(p&&nrSave(c,p,*n)==0);return p;}
static void same(NrContext*c,const uint8_t*p,uint32_t n){uint32_t m;uint8_t*q=save(c,&m);assert(n==m&&!memcmp(p,q,n));free(q);}
static void reject(NrContext*c,uint8_t*p,uint32_t n,const uint8_t*before){uint32_t crc=nrCrc(p+24,n-24);memcpy(p+20,&crc,4);assert(nrLoad(c,p,n)<0);same(c,before,n);}
static void command(NrContext*c,const char*t){assert(nrCommand(c,t,(uint32_t)strlen(t))==0);}
int main(void){
 NrContext*c=malloc(nrContextSize());assert(c&&nrInit(c,nrContextSize(),2030)==0);
 const char*push="{\"op\":\"source-modal\",\"action\":\"push\",\"context\":\"commands\",\"entry\":{\"id\":\"a\",\"kind\":\"center\",\"title\":\"title\",\"body\":\"body\",\"atMs\":0,\"dismissible\":true}}";
 uint32_t initialSize;uint8_t*initial=save(c,&initialSize);assert(nrCommand(c,push,(uint32_t)strlen(push))<0&&!strcmp(nrError(c),"Modal storage required"));same(c,initial,initialSize);
 uint64_t needed=nrModalMemorySize(c);assert(needed>0);uint8_t*arena=malloc(needed+16);assert(arena);memset(arena,0xa5,needed+16);
 assert(nrSetModalMemory(c,0,needed)<0);assert(nrSetModalMemory(c,arena,0)<0);assert(nrSetModalMemory(c,arena+1,needed)<0);assert(nrSetModalMemory(c,arena,needed-1)<0);assert(nrSetModalMemory(c,c,needed)<0);assert(nrSetModalMemory(c,(void*)(UINTPTR_MAX-7),16)<0);assert(nrSetModalMemory(c,arena,needed)==0);
 while(nrCommand(c,push,(uint32_t)strlen(push))<0){assert(!strcmp(nrError(c),"Modal storage required"));same(c,initial,initialSize);uint64_t nextBytes=nrModalMemorySize(c);assert(nextBytes>needed);uint8_t*next=malloc(nextBytes+16);assert(next);memset(next,0xa5,nextBytes+16);assert(nrSetModalMemory(c,next,nextBytes)==0);free(arena);arena=next;needed=nextBytes;}uint32_t n;uint8_t*before=save(c,&n),*bad=malloc(n);assert(bad);
 assert(nrSave(c,arena,n)<0);assert(nrLoad(c,arena,(uint32_t)needed)<0);assert(nrCommand(c,(char*)arena,1)<0);assert(nrSetRenderMemory(c,arena,needed)<0);assert(nrSetPromptMemory(c,arena,needed)<0);assert(nrSetModelMemory(c,arena,needed)<0);assert(nrSetModalMemory(c,arena,needed)<0);same(c,before,n);
 for(int k=0;k<14;k++){memcpy(bad,before,n);SourceModalState*q=(void*)(bad+24+offsetof(State,sourceModal));SourceModalEntry*e=&q->entries[0];switch(k){case 0:q->depth=9;break;case 1:q->scalars=UINT32_MAX;break;case 2:e->title.offset=UINT32_MAX;break;case 3:e->body=e->title;break;case 4:e->reserved=1;break;case 5:e->reserved2=1;break;case 6:e->kind=11;break;case 7:e->dismissible=2;break;case 8:e->id[0]=' ';break;case 9:q->query.offset=1;break;case 10:q->activeCount=1;q->activeIds[0]=1;break;case 11:q->entries[1].title.count=1;break;case 12:{uint32_t x=0xd800;memcpy(bad+n-4,&x,4);break;}case 13:e->atMs=-1;break;}reject(c,bad,n,before);}
 const char *invalid[]={"{\"op\":\"source-modal\",\"action\":\"edit\",\"query\":\"\xc0\xaf\"}","{\"op\":\"source-modal\",\"action\":\"edit\",\"query\":\"\\ud800\"}","{\"op\":\"source-modal\",\"action\":\"edit\",\"query\":null}","{\"op\":\"batch\",\"commands\":[{\"op\":\"source-modal\",\"action\":\"edit\",\"query\":\"changed\"},{\"op\":\"not-an-op\"}]}"};
 for(size_t k=0;k<sizeof(invalid)/sizeof(*invalid);k++){assert(nrCommand(c,invalid[k],(uint32_t)strlen(invalid[k]))<0);same(c,before,n);}
 assert(nrRender(c)>0);uint32_t words[4];assert(nrInfoPage(c,0,arena,8,words,4)<0);assert(nrInfoPage(c,0,0,0,(uint32_t*)arena,4)<0);assert(nrInspectCharacterCell(c,0,0,(NrCharacterCellInfo*)arena,sizeof(NrCharacterCellInfo))<0);same(c,before,n);for(int k=0;k<16;k++)assert(arena[needed+k]==0xa5);
 printf("PASS modal arena aliases, 14 repaired-CRC corruptions, 4 malformed/late commands, pure render; fixed=%zu modal=%zu size=%zu entry=%zu\n",offsetof(State,dynamicPrompt),offsetof(State,sourceModal),sizeof(SourceModalState),sizeof(SourceModalEntry));
 free(initial);free(before);free(bad);free(arena);free(c);return 0;
}
