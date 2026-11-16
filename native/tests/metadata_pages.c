/* Real memory-sanitized calls, retained Unicode source and complete byte windows. */
#include "nocturne_native.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static uint32_t independent_crc32(const unsigned char *bytes,uint32_t count) {
    uint32_t crc=UINT32_MAX;
    for(uint32_t i=0;i<count;i++) {
        crc^=bytes[i];
        for(unsigned bit=0;bit<8;bit++)crc=(crc>>1)^((crc&1)?0xedb88320u:0u);
    }
    return crc^UINT32_MAX;
}
static unsigned occurrences(const char *whole,const char *value) {
    unsigned count=0;size_t length=strlen(value);assert(length);
    for(const char *at=whole;(at=strstr(at,value));at+=length)count++;
    return count;
}
static void retained_sources(NrContext *c) {
    uint32_t scalars[2049];
    for(uint32_t kind=1;kind<=2;kind++)for(uint32_t id=1;id<=(kind==1?24u:12u);id++) {
        assert(nrTextRunSource(c,kind,id,NULL,0)==2048);
        scalars[2048]=0xaabbccddu;
        assert(nrTextRunSource(c,kind,id,scalars,2049)==2048);
        for(unsigned i=0;i<2048;i++)assert(scalars[i]==0x1f642u);
        assert(scalars[2048]==0xaabbccddu);
    }
}

int main(void) {
    void *memory=calloc(1,nrContextSize());assert(memory);
    assert(nrInit(memory,nrContextSize(),8128)==0);NrContext *c=memory;
    char text[8193],command[9000];
    for(int i=0;i<2048;i++)memcpy(text+4*i,"\xf0\x9f\x99\x82",4);
    text[8192]=0;
    for(int i=1;i<=24;i++) {
        int n=snprintf(command,sizeof(command),"{\"op\":\"text\",\"id\":%d,\"text\":\"%s\"}",i,text);
        assert(n>0&&(size_t)n<sizeof(command));assert(nrCommand(c,command,(uint32_t)n)==0);
    }
    for(int i=1;i<=12;i++) {
        int n=snprintf(command,sizeof(command),"{\"op\":\"window\",\"id\":%d,\"title\":\"retained\",\"text\":\"%s\",\"position\":[0,0,16000]}",i,text);
        assert(n>0&&(size_t)n<sizeof(command));assert(nrCommand(c,command,(uint32_t)n)==0);
    }
    const char *borrowed=nrInfo(c);
    assert(strcmp(borrowed,"{\"error\":\"metadata capacity exceeded\"}")!=0);
    size_t legacyLength=strlen(borrowed);
    char *legacy=malloc(legacyLength+1);assert(legacy);
    memcpy(legacy,borrowed,legacyLength+1); /* Paging reuses borrowed scratch. */
    const uint32_t snapshotSize=nrSnapshotSizeFor(c);assert(snapshotSize);
    void *before=malloc(snapshotSize),*after=malloc(snapshotSize);assert(before&&after);
    assert(nrSave(c,before,snapshotSize)==0);
    uint32_t words[4]={0};assert(nrInfoPage(c,0,NULL,0,words,4)==1);
    const uint32_t total=words[0],checksum=words[3];assert(total>262144);
    char *all=malloc((size_t)total+1),*page=malloc(NR_INFO_PAGE_MAX+8);assert(all&&page);
    uint32_t sizes[]={NR_INFO_PAGE_MAX,4093,8192};
    for(unsigned k=0;k<sizeof(sizes)/sizeof(sizes[0]);k++) {
        uint32_t offset=0;
        while(offset<total) {
            memset(page,'Z',NR_INFO_PAGE_MAX+8);
            int result=nrInfoPage(c,offset,page,sizes[k],words,4);
            assert(words[0]==total&&words[3]==checksum&&words[2]==offset+words[1]);
            assert(words[1]&&words[1]<=sizes[k]);assert(result==(words[2]<total));
            for(uint32_t i=words[1];i<NR_INFO_PAGE_MAX+8;i++)assert(page[i]=='Z');
            if(k==0)memcpy(all+offset,page,words[1]);else assert(memcmp(all+offset,page,words[1])==0);
            offset=words[2];
        }
    }
    all[total]=0;
    assert(legacyLength==total&&memcmp(all,legacy,total)==0);
    assert(independent_crc32((const unsigned char*)all,total)==checksum);
    char completeText[8204];
    int textBytes=snprintf(completeText,sizeof(completeText),"\"text\":\"%s\"",text);
    assert(textBytes>0&&(size_t)textBytes<sizeof(completeText));
    assert(occurrences(all,completeText)==36);
    assert(occurrences(all,"\"title\":\"retained\"")==12);
    retained_sources(c);
    uint32_t endWords[6]={1,2,3,4,0xaabbccddu,0x11223344u};
    memset(page,'Z',NR_INFO_PAGE_MAX+8);
    assert(nrInfoPage(c,total,page,NR_INFO_PAGE_MAX,endWords,6)==0);
    assert(endWords[0]==total&&endWords[1]==0&&endWords[2]==total&&endWords[3]==checksum);
    assert(endWords[4]==0xaabbccddu&&endWords[5]==0x11223344u);
    for(unsigned i=0;i<NR_INFO_PAGE_MAX+8;i++)assert(page[i]=='Z');
    uint32_t saved[4];memcpy(saved,words,sizeof(words));
    assert(nrInfoPage(c,UINT32_MAX,page,65536,words,4)==-1);
    assert(memcmp(saved,words,sizeof(words))==0);
    assert(nrInfoPage(c,0,(void*)(UINTPTR_MAX-3),16,words,4)==-1);
    assert(nrInfoPage(c,0,page,16,(uint32_t*)(UINTPTR_MAX-15),4)==-1);
    assert(nrInfoPage(c,0,memory,16,words,4)==-1);
    assert(nrInfoPage(c,0,page,16,(uint32_t*)memory,4)==-1);
    assert(nrInfoPage(c,0,page,16,(uint32_t*)(page+4),4)==-1);
    assert(memcmp(saved,words,sizeof(words))==0);
    assert(nrSave(c,after,snapshotSize)==0);assert(memcmp(before,after,snapshotSize)==0);
    printf("complete metadata pages: %u bytes; CRC32 %08x; all buffers, page sizes and snapshot checks PASS\n",total,checksum);
    free(legacy);free(page);free(all);free(after);free(before);free(memory);return 0;
}
